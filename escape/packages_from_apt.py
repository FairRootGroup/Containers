#! /usr/bin/python3

from argparse import ArgumentParser
from pathlib import Path
import glob
from pprint import pprint
from re import sub
from apt import Cache

from ruamel.yaml import YAML


def get_upstream_version(v):
    for pat, repl in (
                (r'^[0-9]+:', r''),
                (r'-[^-]*$', r''),
                (r'[.+](dfsg|debian)', r''),
                (r'[+][0-9]{8}', r''),
            ):
        v = sub(pat, repl, v)
    return v


class PackagesYamlSink(object):
    # Represents a modifiable instance of a packages.yaml
    # (interface)
    # Could be in memory, could be file, whatever
    # Has to handle all the details
    def add_entry(self, package_name, spec, path, buildable=None):
        """
        Append an entry, if it does not exist yet

        package_name: Something like 'cmake'
        spec: Something like 'cmake@foo +variant os=bar'
        path: Something like '/usr'
        buildable:
          None: Do not modify
          True/False: Set to true/false
        """
        raise NotImplementedError()


class PackagesYamlOldFile(PackagesYamlSink):
    def __init__(self, packages_filename):
        self.yaml = YAML()
        self.packages_filename = Path(packages_filename)
        self.conf: dict = {}
        self.packages_yaml = {'packages': self.conf}

    def load(self):
        try:
            self.packages_yaml = self.yaml.load(self.packages_filename)
        except FileNotFoundError:
            self.packages_yaml = {}
        self.conf = self.packages_yaml.setdefault('packages', {})

    def safe(self):
        self.yaml.dump(self.packages_yaml, self.packages_filename)

    def add_entry(self, package_name, spec, path, buildable=None):
        e = self.conf.setdefault(package_name, {})
        if buildable is not None:
            # e.setdefault('buildable', buildable)
            e['buildable'] = buildable
        if spec is None or path is None:
            return
        e = e.setdefault('paths', {})
        e[spec] = path


class MapEntry(object):
    spack_name = None
    # Put "os=debian10" in here:
    base_selector = None
    variant = None
    prefixes = None
    sys_pkg_names = None
    buildable = None


class MapFile(object):
    def __init__(self, map_filename):
        self.yaml = YAML()
        self.map_filename = Path(map_filename)
        self.map_entries = self.yaml.load(self.map_filename)

    def __iter__(self):
        for yaml_entry in self.map_entries['mapping']:
            entry = MapEntry()

            entry.spack_name = yaml_entry['name']
            entry.sys_pkg_names = yaml_entry.get('pkg_names', None)
            entry.variant = yaml_entry.get('variant', None)
            entry.prefixes = yaml_entry.get('prefixes', None)
            entry.buildable = yaml_entry.get('buildable', None)

            yield entry


class PackagesFromApt(object):
    def __init__(self, packages_sink):
        self.cache = Cache()
        self.missing: set = set()
        self.sink = packages_sink

    def fill_entry_defaults(self, entry):
        if entry.prefixes is None:
            entry.prefixes = ['/usr']
        elif '/usr' not in entry.prefixes:
            entry.prefixes.append('/usr')
        if entry.base_selector is None:
            entry.base_selector = 'os=debian10'
        if entry.sys_pkg_names is not None and entry.buildable is None:
            entry.buildable = False

    def do_entry(self, entry):
        version_set = set()
        if entry.sys_pkg_names is None and entry.buildable is not None:
            self.sink.add_entry(entry.spack_name, None, None, entry.buildable)
            return
        for name in entry.sys_pkg_names:
            try:
                pkg = self.cache[name]
            except KeyError:
                self.missing.add(name)
                return
            if pkg.installed is None:
                self.missing.add(name)
                return
            version_set.add(pkg.installed.version)
        # pprint(version_set)
        if len(version_set) == 0:
            # not installed at all
            return
        if len(version_set) > 1:
            # Inconsistent versions
            return
        version = version_set.pop()
        version = get_upstream_version(version)

        prefix = None
        for entry_prefix in entry.prefixes:
            found = glob.glob(entry_prefix)
            if len(found) > 1:
                print("Found multiple paths for {}, taking first:"
                      .format(entry_prefix))
                pprint(found)
            if len(found) > 0:
                prefix = found[0]
                break
        if prefix is None:
            print("Prefix not found for {}".format(entry.spack_name))

        spec = "{}@{}".format(entry.spack_name, version)
        if entry.variant:
            spec += " {}".format(entry.variant)
        if entry.base_selector:
            spec += " {}".format(entry.base_selector)
        self.sink.add_entry(entry.spack_name, spec, prefix, entry.buildable)

    def do_simple(self, spack_name, sys_pkg_names, variant=None, prefixes=None,
                  buildable=None):
        entry = MapEntry()
        entry.spack_name = spack_name
        entry.sys_pkg_names = sys_pkg_names
        entry.variant = variant
        entry.prefixes = prefixes
        entry.buildable = buildable
        self.fill_entry_defaults(entry)
        self.do_entry(entry)

    def do_map_file(self, map_file):
        pass

    def print_missing(self):
        if len(self.missing) == 0:
            return
        print("Consider installing the following packages:")
        pprint(self.missing)


def builtin_mapping(pfa) -> None:
    pfa.do_simple('libc', ('libc6-dev',), variant='+iconv')
    pfa.do_simple('gettext', ('gettext',))
    pfa.do_simple("zlib", ("zlib1g-dev",))
    pfa.do_simple('lz4', ('liblz4-dev',))
    pfa.do_simple('bzip2', ('libbz2-dev', 'bzip2'))
    pfa.do_simple('zstd', ('libzstd-dev',))
    pfa.do_simple('xxhash', ('libxxhash-dev',))
    pfa.do_simple("perl", ("perl",))
    pfa.do_simple("diffutils", ("diffutils",))
    pfa.do_simple("git", ("git",))
    pfa.do_simple('squashfs', ('squashfs-tools',))
    pfa.do_simple('libseccomp', ('libseccomp-dev',))
    pfa.do_simple('gawk', ('gawk',))
    pfa.do_simple('shadow', ('login', 'passwd', 'uidmap'))
    pfa.do_simple('cryptsetup', ('cryptsetup-bin',))
    pfa.do_simple('openssl', ('libssl-dev',))
    pfa.do_simple('pkgconf', ('pkgconf',))
    pfa.do_simple('libgpg-error', ('libgpg-error-dev',))
    pfa.do_simple('ncurses', ('libncurses-dev',))
    pfa.do_simple('readline', ('libreadline-dev',))
    pfa.do_simple('ninja', ('ninja-build',))
    pfa.do_simple('rsync', ('rsync',))
    pfa.do_simple('expat', ('libexpat1-dev',))
    pfa.do_simple('xerces-c', ('libxerces-c-dev',), variant='cxxstd=11')
    pfa.do_simple('msgpack-c', ('libmsgpack-dev',), buildable=True)
    pfa.do_simple('libxml2', ('libxml2-dev',))
    pfa.do_simple('pcre', ('libpcre3-dev',))
    pfa.do_simple('xcb-proto', ('xcb-proto',))
    pfa.do_simple('m4', ('m4',))
    pfa.do_simple('tar', ('tar',))
    pfa.do_simple('gdbm', ('libgdbm-dev',))
    pfa.do_simple('davix', ('davix-dev',))
    pfa.do_simple('libxau', ('libxau-dev',))
    pfa.do_simple('libxcb', ('libxcb1-dev',))
    pfa.do_simple('libx11', ('libx11-dev',))
    pfa.do_simple('libxext', ('libxext-dev',))
    pfa.do_simple('libxrender', ('libxrender-dev',))
    pfa.do_simple('libsm', ('libsm-dev',))
    pfa.do_simple('libice', ('libice-dev',))
    pfa.do_simple('xz', ('liblzma-dev', 'xz-utils'))
    pfa.do_simple('autoconf', ('autoconf',))
    pfa.do_simple('automake', ('automake',))
    pfa.do_simple('fontconfig', ('libfontconfig1-dev',))
    pfa.do_simple('freetype', ('libfreetype6-dev',))
    pfa.do_simple('libxft', ('libxft-dev',))
    pfa.do_simple('sqlite', ('libsqlite3-dev',))
    pfa.do_simple('libxpm', ('libxpm-dev',))
    pfa.do_simple('libjpeg-turbo', ('libjpeg62-turbo-dev',))
    pfa.do_simple('libpng', ('libpng-dev',))
    pfa.do_simple('binutils', ('binutils',))
    pfa.do_simple('util-linux', ('uuid-dev',), variant='+libuuid')
    pfa.do_simple('flex', ('flex',))
    pfa.do_simple('bison', ('bison',))
    pfa.do_simple('libzmq', ('libzmq3-dev',))
    pfa.do_simple('pmix', ('libpmix-dev',), prefixes=['/usr/lib/*/pmix'])
    # Debian has +llvm really, but our specs want ~llvm
    pfa.do_simple('mesa', ('libgl1-mesa-dev',), variant='~llvm')
    pfa.do_simple('openglu', None, buildable=False)
    pfa.do_simple('mesa-glu', ('libglu1-mesa-dev',))
    pfa.do_simple('glew', ('libglew-dev',))
    pfa.do_simple('ftgl', ('libftgl-dev',))
    pfa.do_simple('libffi', ('libffi-dev',))
    pfa.do_simple('gsl', ('libgsl-dev',))
    # pfa.do_simple('openblas', ('libopenblas-dev',))


def create_parser() -> ArgumentParser:
    parser = ArgumentParser()
    parser.add_argument('-M', dest='mappingfiles', action='append',
                        help='Give (yaml) mapping file '
                        '(allowed multiple times)')
    parser.add_argument('-o', dest='filename', required=True)
    return parser


def main() -> None:
    parser = create_parser()
    args = parser.parse_args()
    pprint(args)

    sink = PackagesYamlOldFile(args.filename)
    sink.load()

    pfa = PackagesFromApt(sink)
    if args.mappingfiles is not None:
        for mf in map(MapFile, args.mappingfiles):
            for entry in mf:
                pfa.fill_entry_defaults(entry)
                pfa.do_entry(entry)
    else:
        builtin_mapping(pfa)
    pfa.print_missing()
    sink.safe()


if __name__ == '__main__':
    main()
