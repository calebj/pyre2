import io
import os
import re
import sys
import platform
from setuptools import setup, Extension, Command

MINIMUM_CYTHON_VERSION = '0.20'
BASE_DIR = os.path.dirname(__file__)
PY2 = sys.version_info[0] == 2
DEBUG = False


re2_lib = ('re2', {
    'sources': [
        "re2/re2/bitstate.cc",
        "re2/re2/compile.cc",
        "re2/re2/dfa.cc",
        "re2/re2/filtered_re2.cc",
        "re2/re2/mimics_pcre.cc",
        "re2/re2/nfa.cc",
        "re2/re2/onepass.cc",
        "re2/re2/parse.cc",
        "re2/re2/perl_groups.cc",
        "re2/re2/prefilter.cc",
        "re2/re2/prefilter_tree.cc",
        "re2/re2/prog.cc",
        "re2/re2/re2.cc",
        "re2/re2/regexp.cc",
        "re2/re2/set.cc",
        "re2/re2/simplify.cc",
        "re2/re2/stringpiece.cc",
        "re2/re2/tostring.cc",
        "re2/re2/unicode_casefold.cc",
        "re2/re2/unicode_groups.cc",
        "re2/util/rune.cc",
        "re2/util/strutil.cc"
    ],
    'include_dirs': ['re2']
})


class TestCommand(Command):
    description = 'Run packaged tests'
    user_options = []
    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        from tests import re2_test
        re2_test.testall()


def majorminor(version):
    return [int(x) for x in re.match(r'([0-9]+)\.([0-9]+)', version).groups()]


def get_long_description():
    with io.open(os.path.join(BASE_DIR, 'README.rst'), encoding='utf8') as inp:
        return inp.read()


def get_authors():
    author_re = re.compile(r'^\s*(.*?)\s+<.*?\@.*?>', re.M)
    authors_f = open(os.path.join(BASE_DIR, 'AUTHORS'))
    authors = [match.group(1) for match in author_re.finditer(authors_f.read())]
    authors_f.close()
    return ', '.join(authors)


if '--cython' in sys.argv or not os.path.exists('src/re2.cpp'):
    # Using Cython
    try:
        sys.argv.remove('--cython')
    except ValueError:
        pass

    from Cython.Compiler.Main import Version

    if majorminor(MINIMUM_CYTHON_VERSION) >= majorminor(Version.version):
        raise ValueError('Cython is version %s, but needs to be at least %s.'
                % (Version.version, MINIMUM_CYTHON_VERSION))

    from Cython.Distutils import build_ext
    from Cython.Build import cythonize
    use_cython = True
else:
    # Building from C
    from setuptools.command.build_ext import build_ext
    use_cython = False


class custom_build_ext(build_ext):
    def run(self):
        if self.distribution.has_c_libraries():
            build_clib = self.get_finalized_command('build_clib')
            self.libraries.extend(build_clib.get_library_names() or [])
            self.library_dirs.insert(0, build_clib.build_clib)

        build_ext.run(self)


cmdclass = {'test': TestCommand, 'build_ext': custom_build_ext}
os.environ['GCC_COLORS'] = 'auto'
extra_compile_args = ['-std=c++11', '-DPY2=%d' % PY2]
extra_compile_args.extend(['-O0', '-g'] if DEBUG else ['-O3', '-march=native', '-DNDEBUG'])
extra_link_args = ['-g'] if DEBUG else ['-DNDEBUG']

if sys.platform == 'darwin':
    extra_compile_args.extend(['-mmacosx-version-min=10.7', '-stdlib=libc++'])

re2_lib[1]['cflags'] = extra_compile_args

ext_modules = [
    Extension(
        're2',
        sources=['src/re2.pyx' if use_cython else 'src/re2.cpp'],
        language='c++',
        include_dirs=['re2'],
        libraries=['re2'],
        extra_compile_args=extra_compile_args,
        extra_link_args=extra_link_args,
    )
]

if use_cython:
    ext_modules = cythonize(
        ext_modules,
        language_level=3,
        annotate=True,
        compiler_directives={
            'embedsignature': True,
            'warn.unused': True,
            'warn.unreachable': True,
        }
    )


setup(
    name='re2-wheels',
    version='0.2.23',
    description='Python wrapper for Google\'s RE2 using Cython',
    long_description=get_long_description(),
    author=get_authors(),
    license='New BSD License',
    author_email = 'me@calebj.io',
    url = 'http://github.com/calebj/pyre2/',
    ext_modules = ext_modules,
    libraries=[re2_lib],
    cmdclass=cmdclass,
    classifiers = [
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Cython',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
