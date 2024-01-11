# We are building with clang for faster/lower memory LTO builds.
# See https://docs.fedoraproject.org/en-US/packaging-guidelines/#_compiler_macros
%global toolchain clang

# Components enabled if supported by target architecture:
%define gold_arches %{ix86} x86_64 %{arm} aarch64 %{power64} s390x
%ifarch %{gold_arches}
  %bcond_without gold
%else
  %bcond_with gold
%endif

%bcond_with compat_build
%bcond_without check

#global rc_ver 3
%global maj_ver 15
%global min_ver 0
%global patch_ver 7
%global llvm_srcdir llvm-%{maj_ver}.%{min_ver}.%{patch_ver}%{?rc_ver:rc%{rc_ver}}.src
%global cmake_srcdir cmake-%{maj_ver}.%{min_ver}.%{patch_ver}%{?rc_ver:rc%{rc_ver}}.src

%if %{with compat_build}
%global pkg_name llvm%{maj_ver}
%global exec_suffix -%{maj_ver}
%global install_prefix %{_libdir}/%{name}
%global install_bindir %{install_prefix}/bin
%global install_includedir %{install_prefix}/include
%global install_libdir %{install_prefix}/lib

%global pkg_bindir %{install_bindir}
%global pkg_includedir %{_includedir}/%{name}
%global pkg_libdir %{install_libdir}
%else
%global pkg_name llvm
%global install_prefix /usr
%global install_libdir %{_libdir}
%global pkg_bindir %{_bindir}
%global pkg_libdir %{install_libdir}
%global exec_suffix %{nil}
%endif

%global build_install_prefix %{buildroot}%{install_prefix}

# Lower memory usage of dwz on s390x
%global _dwz_low_mem_die_limit_s390x 1
%global _dwz_max_die_limit_s390x 1000000

# https://fedoraproject.org/wiki/Changes/PythonSafePath#Opting_out
# Don't add -P to Python shebangs
# The executable Python scripts in /usr/share/opt-viewer/ import each other
%undefine _py3_shebang_P

%global llvm_triple %{_host}
################################################################################
# OS Specific Configuration
################################################################################

########
# RHEL #
########
%if 0%{?rhel}
%global targets_to_build "X86;AMDGPU;PowerPC;NVPTX;SystemZ;AArch64;ARM;Mips;BPF;WebAssembly"
%global experimental_targets_to_build ""
%global _smp_mflags -j8

%if 0%{?rhel} == 8
%undefine __cmake_in_source_build

# libedit-devel is a buildroot-only package in RHEL8, so we can't have a
# any run-time depencies on it.
%global use_libedit 0
%endif

%if 0%{?rhel} > 8
%global use_libedit 1
%endif

%else
##########
# FEDORA #
##########
%global targets_to_build "all"
%global experimental_targets_to_build "AVR"
%endif

################################################################################
# Spec File
################################################################################


Name:		%{pkg_name}
Version:	%{maj_ver}.%{min_ver}.%{patch_ver}%{?rc_ver:~rc%{rc_ver}}
Release:	1%{?dist}
Summary:	The Low Level Virtual Machine

License:	NCSA
URL:		http://llvm.org
Source0:	https://github.com/llvm/llvm-project/releases/download/llvmorg-%{maj_ver}.%{min_ver}.%{patch_ver}%{?rc_ver:-rc%{rc_ver}}/%{llvm_srcdir}.tar.xz
Source1:	https://github.com/llvm/llvm-project/releases/download/llvmorg-%{maj_ver}.%{min_ver}.%{patch_ver}%{?rc_ver:-rc%{rc_ver}}/%{llvm_srcdir}.tar.xz.sig
Source2:	https://github.com/llvm/llvm-project/releases/download/llvmorg-%{maj_ver}.%{min_ver}.%{patch_ver}%{?rc_ver:-rc%{rc_ver}}/%{cmake_srcdir}.tar.xz
Source3:	https://github.com/llvm/llvm-project/releases/download/llvmorg-%{maj_ver}.%{min_ver}.%{patch_ver}%{?rc_ver:-rc%{rc_ver}}/%{cmake_srcdir}.tar.xz.sig
Source4:	release-keys.asc

%if %{without compat_build}
Source5:	run-lit-tests
Source6:	lit.fedora.cfg.py
%endif

Patch2:		0001-XFAIL-missing-abstract-variable.ll-test-on-ppc64le.patch

# RHEL-specific patches.
Patch101:      0001-Deactivate-markdown-doc.patch

BuildRequires:	gcc
BuildRequires:	gcc-c++
BuildRequires:	clang
BuildRequires:	cmake
BuildRequires:	ninja-build
BuildRequires:	zlib-devel
BuildRequires:	libffi-devel
BuildRequires:	ncurses-devel
BuildRequires:	python3-psutil
BuildRequires:	python3-sphinx
BuildRequires:	multilib-rpm-config
%if %{with gold}
BuildRequires:	binutils-devel
%endif
%ifarch %{valgrind_arches}
# Enable extra functionality when run the LLVM JIT under valgrind.
BuildRequires:	valgrind-devel
%endif
%if 0%{?use_libedit}
# LLVM's LineEditor library will use libedit if it is available.
BuildRequires:	libedit-devel
%endif
# Need pandoc to cover markdown to rst, because RHEL does not have recommonmark,
# so we can't build the documentation as is.
%if !0%{?rhel}
BuildRequires:	python3-recommonmark
%endif
%if 0%{?rhel} == 8
# RHEL8 has pandoc which we can use instead of python3-recommonmark for some things.
BuildRequires:	pandoc
%endif
# We need python3-devel for pathfix.py and %%py3_shebang_fix.
BuildRequires:	python3-devel
BuildRequires:	python3-setuptools

# For origin certification
BuildRequires:	gnupg2


Requires:	%{name}-libs%{?_isa} = %{version}-%{release}

Provides:	llvm(major) = %{maj_ver}

%description
LLVM is a compiler infrastructure designed for compile-time, link-time,
runtime, and idle-time optimization of programs from arbitrary programming
languages. The compiler infrastructure includes mirror sets of programming
tools as well as libraries with equivalent functionality.

%package devel
Summary:	Libraries and header files for LLVM
Requires:	%{name}%{?_isa} = %{version}-%{release}
Requires:	%{name}-libs%{?_isa} = %{version}-%{release}
# The installed LLVM cmake files will add -ledit to the linker flags for any
# app that requires the libLLVMLineEditor, so we need to make sure
# libedit-devel is available.
%if 0%{?use_libedit}
Requires:	libedit-devel
%endif
# The installed cmake files reference binaries from llvm-test and llvm-static.
# We tried in the past to split the cmake exports for these binaries out into
# separate files, so that llvm-devel would not need to Require these packages,
# but this caused bugs (rhbz#1773678) and forced us to carry two non-upstream
# patches.
Requires:	%{name}-static%{?_isa} = %{version}-%{release}
%if %{without compat_build}
Requires:	%{name}-test%{?_isa} = %{version}-%{release}
%endif


Requires(post):	%{_sbindir}/alternatives
Requires(postun):	%{_sbindir}/alternatives

Provides:	llvm-devel(major) = %{maj_ver}

%description devel
This package contains library and header files needed to develop new native
programs that use the LLVM infrastructure.

%package doc
Summary:	Documentation for LLVM
BuildArch:	noarch
Requires:	%{name} = %{version}-%{release}

%description doc
Documentation for the LLVM compiler infrastructure.

%package libs
Summary:	LLVM shared libraries

%description libs
Shared libraries for the LLVM compiler infrastructure.

%package static
Summary:	LLVM static libraries
Conflicts:	%{name}-devel < 8

Provides:	llvm-static(major) = %{maj_ver}

%description static
Static libraries for the LLVM compiler infrastructure.

%if %{without compat_build}

%package test
Summary:	LLVM regression tests
Requires:	%{name}%{?_isa} = %{version}-%{release}
Requires:	%{name}-libs%{?_isa} = %{version}-%{release}

Provides:	llvm-test(major) = %{maj_ver}

%description test
LLVM regression tests.

%package googletest
Summary: LLVM's modified googletest sources

%description googletest
LLVM's modified googletest sources.

%if 0%{?rhel}
%package toolset
Summary:	Package that installs llvm-toolset
Requires:	clang = %{version}
Requires:	llvm = %{version}

%ifnarch s390x
Requires:	lld = %{version}
%endif

%description toolset
This is the main package for llvm-toolset.
%endif

%endif

%prep
%{gpgverify} --keyring='%{SOURCE4}' --signature='%{SOURCE1}' --data='%{SOURCE0}'
%{gpgverify} --keyring='%{SOURCE4}' --signature='%{SOURCE3}' --data='%{SOURCE2}'
%setup -T -q -b 2 -n %{cmake_srcdir}
# TODO: It would be more elegant to set -DLLVM_COMMON_CMAKE_UTILS=%{_builddir}/%{cmake_srcdir},
# but this is not a CACHED variable, so we can't actually set it externally :(
cd ..
mv %{cmake_srcdir} cmake
%autosetup -n %{llvm_srcdir} -p2

%py3_shebang_fix \
	test/BugPoint/compile-custom.ll.py \
	tools/opt-viewer/*.py \
	utils/update_cc_test_checks.py

%if 0%{?rhel} == 8
# Convert markdown files to rst to cope with the absence of compatible md parser in rhel.
# The sed expression takes care of a slight difference between pandoc markdown and sphinx markdown.
find -name '*.md' | while read md; do sed -r -e 's/^( )*\* /\n\1\* /' ${md} | pandoc -f markdown -o ${md%.md}.rst  ; done
%endif

%build

%ifarch s390 s390x
# Fails with "exceeded PCRE's backtracking limit"
%global _lto_cflags %nil
%else
%global _lto_cflags -flto=thin
%endif

%ifarch s390 s390x %{arm} %ix86
# Decrease debuginfo verbosity to reduce memory consumption during final library linking
%global optflags %(echo %{optflags} | sed 's/-g /-g1 /')
%endif

# force off shared libs as cmake macros turns it on.
%cmake	-G Ninja \
	-DBUILD_SHARED_LIBS:BOOL=OFF \
	-DLLVM_PARALLEL_LINK_JOBS=1 \
	-DCMAKE_BUILD_TYPE=RelWithDebInfo \
	-DCMAKE_SKIP_RPATH:BOOL=ON \
%ifarch s390 %{arm} %ix86
	-DCMAKE_C_FLAGS_RELWITHDEBINFO="%{optflags} -DNDEBUG" \
	-DCMAKE_CXX_FLAGS_RELWITHDEBINFO="%{optflags} -DNDEBUG" \
%endif
%if %{without compat_build}
%if 0%{?__isa_bits} == 64
	-DLLVM_LIBDIR_SUFFIX=64 \
%else
	-DLLVM_LIBDIR_SUFFIX= \
%endif
%endif
	\
	-DLLVM_TARGETS_TO_BUILD=%{targets_to_build} \
	-DLLVM_ENABLE_LIBCXX:BOOL=OFF \
	-DLLVM_ENABLE_ZLIB:BOOL=ON \
	-DLLVM_ENABLE_FFI:BOOL=ON \
	-DLLVM_ENABLE_RTTI:BOOL=ON \
	-DLLVM_USE_PERF:BOOL=ON \
%if %{with gold}
	-DLLVM_BINUTILS_INCDIR=%{_includedir} \
%endif
	-DLLVM_EXPERIMENTAL_TARGETS_TO_BUILD=%{experimental_targets_to_build} \
	\
	-DLLVM_BUILD_RUNTIME:BOOL=ON \
	\
	-DLLVM_INCLUDE_TOOLS:BOOL=ON \
	-DLLVM_BUILD_TOOLS:BOOL=ON \
	\
	-DLLVM_INCLUDE_TESTS:BOOL=ON \
	-DLLVM_BUILD_TESTS:BOOL=ON \
	-DLLVM_LIT_ARGS=-v \
	\
	-DLLVM_INCLUDE_EXAMPLES:BOOL=ON \
	-DLLVM_BUILD_EXAMPLES:BOOL=OFF \
	\
	-DLLVM_INCLUDE_UTILS:BOOL=ON \
%if %{with compat_build}
	-DLLVM_INSTALL_UTILS:BOOL=OFF \
%else
	-DLLVM_INSTALL_UTILS:BOOL=ON \
	-DLLVM_UTILS_INSTALL_DIR:PATH=%{_bindir} \
	-DLLVM_TOOLS_INSTALL_DIR:PATH=bin \
%endif
	\
	-DLLVM_INCLUDE_DOCS:BOOL=ON \
	-DLLVM_BUILD_DOCS:BOOL=ON \
	-DLLVM_ENABLE_SPHINX:BOOL=ON \
	-DLLVM_ENABLE_DOXYGEN:BOOL=OFF \
	\
%if %{without compat_build}
	-DLLVM_VERSION_SUFFIX='' \
%endif
	-DLLVM_BUILD_LLVM_DYLIB:BOOL=ON \
	-DLLVM_LINK_LLVM_DYLIB:BOOL=ON \
	-DLLVM_BUILD_EXTERNAL_COMPILER_RT:BOOL=ON \
	-DLLVM_INSTALL_TOOLCHAIN_ONLY:BOOL=OFF \
	\
	-DLLVM_DEFAULT_TARGET_TRIPLE=%{llvm_triple} \
	-DSPHINX_WARNINGS_AS_ERRORS=OFF \
	-DCMAKE_INSTALL_PREFIX=%{install_prefix} \
	-DLLVM_INSTALL_SPHINX_HTML_DIR=%{_pkgdocdir}/html \
	-DSPHINX_EXECUTABLE=%{_bindir}/sphinx-build-3 \
	-DLLVM_INCLUDE_BENCHMARKS=OFF

# Build libLLVM.so first.  This ensures that when libLLVM.so is linking, there
# are no other compile jobs running.  This will help reduce OOM errors on the
# builders without having to artificially limit the number of concurrent jobs.
%cmake_build --target LLVM
%cmake_build

%install
%cmake_install

mkdir -p %{buildroot}/%{_bindir}

%if %{without compat_build}

# Fix some man pages
ln -s llvm-config.1 %{buildroot}%{_mandir}/man1/llvm-config%{exec_suffix}-%{__isa_bits}.1

# Install binaries needed for lit tests
%global test_binaries llvm-isel-fuzzer llvm-opt-fuzzer

for f in %{test_binaries}
do
    install -m 0755 %{_vpath_builddir}/bin/$f %{buildroot}%{_bindir}
done

# Remove testing of update utility tools
rm -rf test/tools/UpdateTestChecks

%multilib_fix_c_header --file %{_includedir}/llvm/Config/llvm-config.h

# Install libraries needed for unittests
%if 0%{?__isa_bits} == 64
%global build_libdir %{_vpath_builddir}/lib64
%else
%global build_libdir %{_vpath_builddir}/lib
%endif

install %{build_libdir}/libLLVMTestingSupport.a %{buildroot}%{_libdir}

%global install_srcdir %{buildroot}%{_datadir}/llvm/src

# Install gtest sources so clang can use them for gtest
install -d %{install_srcdir}
install -d %{install_srcdir}/utils/
cp -R utils/unittest %{install_srcdir}/utils/

# Clang needs these for running lit tests.
cp utils/update_cc_test_checks.py %{install_srcdir}/utils/
cp -R utils/UpdateTestChecks %{install_srcdir}/utils/

%if %{with gold}
# Add symlink to lto plugin in the binutils plugin directory.
%{__mkdir_p} %{buildroot}%{_libdir}/bfd-plugins/
ln -s -t %{buildroot}%{_libdir}/bfd-plugins/ ../LLVMgold.so
%endif

%else

# Add version suffix to binaries
for f in %{buildroot}/%{install_bindir}/*; do
  filename=`basename $f`
  ln -s ../../%{install_bindir}/$filename %{buildroot}/%{_bindir}/$filename%{exec_suffix}
done

# Move header files
mkdir -p %{buildroot}/%{pkg_includedir}
ln -s ../../../%{install_includedir}/llvm %{buildroot}/%{pkg_includedir}/llvm
ln -s ../../../%{install_includedir}/llvm-c %{buildroot}/%{pkg_includedir}/llvm-c

# Fix multi-lib
%multilib_fix_c_header --file %{install_includedir}/llvm/Config/llvm-config.h

# Create ld.so.conf.d entry
mkdir -p %{buildroot}%{_sysconfdir}/ld.so.conf.d
cat >> %{buildroot}%{_sysconfdir}/ld.so.conf.d/%{name}-%{_arch}.conf << EOF
%{pkg_libdir}
EOF

# Add version suffix to man pages and move them to mandir.
mkdir -p %{buildroot}/%{_mandir}/man1
for f in %{build_install_prefix}/share/man/man1/*; do
  filename=`basename $f | cut -f 1 -d '.'`
  mv $f %{buildroot}%{_mandir}/man1/$filename%{exec_suffix}.1
done

# Remove opt-viewer, since this is just a compatibility package.
rm -Rf %{build_install_prefix}/share/opt-viewer

%endif

# llvm-config special casing. llvm-config is managed by update-alternatives.
# the original file must remain available for compatibility with the CMake
# infrastructure. Without compat, cmake points to the symlink, with compat it
# points to the original file.

%if %{without compat_build}

mv %{buildroot}/%{pkg_bindir}/llvm-config %{buildroot}/%{pkg_bindir}/llvm-config%{exec_suffix}-%{__isa_bits}
# We still maintain a versionned symlink for consistency across llvm versions.
# This is specific to the non-compat build and matches the exec prefix for
# compat builds. An isa-agnostic versionned symlink is also maintained in the (un)install
# steps.
(cd %{buildroot}/%{pkg_bindir} ; ln -s llvm-config%{exec_suffix}-%{__isa_bits} llvm-config-%{maj_ver}-%{__isa_bits} )
# ghost presence
touch %{buildroot}%{_bindir}/llvm-config-%{maj_ver}

%else

rm %{buildroot}%{_bindir}/llvm-config%{exec_suffix}
(cd %{buildroot}/%{pkg_bindir} ; ln -s llvm-config llvm-config%{exec_suffix}-%{__isa_bits} )

%endif

# ghost presence
touch %{buildroot}%{_bindir}/llvm-config%{exec_suffix}

%if %{without compat_build}
cp -Rv ../cmake/Modules/* %{buildroot}%{_libdir}/cmake/llvm
%endif


%check
# Disable check section on arm due to some kind of memory related failure.
# Possibly related to https://bugzilla.redhat.com/show_bug.cgi?id=1920183
%ifnarch %{arm}

# TODO: Fix the failures below
%ifarch %{arm}
rm test/tools/llvm-readobj/ELF/dependent-libraries.test
%endif

# non reproducible errors
rm test/tools/dsymutil/X86/swift-interface.test

%if %{with check}
# FIXME: use %%cmake_build instead of %%__ninja
LD_LIBRARY_PATH=%{buildroot}/%{pkg_libdir}  %{__ninja} check-all -C %{_vpath_builddir}
%endif

%endif

%ldconfig_scriptlets libs

%post devel
%{_sbindir}/update-alternatives --install %{_bindir}/llvm-config%{exec_suffix} llvm-config%{exec_suffix} %{pkg_bindir}/llvm-config%{exec_suffix}-%{__isa_bits} %{__isa_bits}
%if %{without compat_build}
%{_sbindir}/update-alternatives --install %{_bindir}/llvm-config-%{maj_ver} llvm-config-%{maj_ver} %{pkg_bindir}/llvm-config%{exec_suffix}-%{__isa_bits} %{__isa_bits}
%endif

%postun devel
if [ $1 -eq 0 ]; then
  %{_sbindir}/update-alternatives --remove llvm-config%{exec_suffix} %{pkg_bindir}/llvm-config%{exec_suffix}-%{__isa_bits}
%if %{without compat_build}
  %{_sbindir}/update-alternatives --remove llvm-config-%{maj_ver} %{pkg_bindir}/llvm-config%{exec_suffix}-%{__isa_bits}
%endif
fi

%files
%license LICENSE.TXT
%exclude %{_mandir}/man1/llvm-config*
%{_mandir}/man1/*
%{_bindir}/*

%exclude %{_bindir}/llvm-config%{exec_suffix}
%exclude %{pkg_bindir}/llvm-config%{exec_suffix}-%{__isa_bits}

%if %{without compat_build}
%exclude %{_bindir}/llvm-config-%{maj_ver}
%exclude %{pkg_bindir}/llvm-config-%{maj_ver}-%{__isa_bits}
%exclude %{_bindir}/not
%exclude %{_bindir}/count
%exclude %{_bindir}/yaml-bench
%exclude %{_bindir}/lli-child-target
%exclude %{_bindir}/llvm-isel-fuzzer
%exclude %{_bindir}/llvm-opt-fuzzer
%{_datadir}/opt-viewer
%else
%{pkg_bindir}
%endif

%files libs
%license LICENSE.TXT
%{pkg_libdir}/libLLVM-%{maj_ver}.so
%if %{without compat_build}
%if %{with gold}
%{_libdir}/LLVMgold.so
%{_libdir}/bfd-plugins/LLVMgold.so
%endif
%{_libdir}/libLLVM-%{maj_ver}.%{min_ver}*.so
%{_libdir}/libLTO.so*
%else
%config(noreplace) %{_sysconfdir}/ld.so.conf.d/%{name}-%{_arch}.conf
%if %{with gold}
%{_libdir}/%{name}/lib/LLVMgold.so
%endif
%{pkg_libdir}/libLLVM-%{maj_ver}.%{min_ver}*.so
%{pkg_libdir}/libLTO.so*
%exclude %{pkg_libdir}/libLTO.so
%endif
%{pkg_libdir}/libRemarks.so*

%files devel
%license LICENSE.TXT

%ghost %{_bindir}/llvm-config%{exec_suffix}
%{pkg_bindir}/llvm-config%{exec_suffix}-%{__isa_bits}
%{_mandir}/man1/llvm-config*

%if %{without compat_build}
%{_includedir}/llvm
%{_includedir}/llvm-c
%{_libdir}/libLLVM.so
%{_libdir}/cmake/llvm
%{pkg_bindir}/llvm-config-%{maj_ver}-%{__isa_bits}
%ghost %{_bindir}/llvm-config-%{maj_ver}
%else
%{install_includedir}/llvm
%{install_includedir}/llvm-c
%{pkg_includedir}/llvm
%{pkg_includedir}/llvm-c
%{pkg_libdir}/libLTO.so
%{pkg_libdir}/libLLVM.so
%{pkg_libdir}/cmake/llvm
%endif

%files doc
%license LICENSE.TXT
%doc %{_pkgdocdir}/html

%files static
%license LICENSE.TXT
%if %{without compat_build}
%{_libdir}/*.a
%exclude %{_libdir}/libLLVMTestingSupport.a
%else
%{_libdir}/%{name}/lib/*.a
%endif

%if %{without compat_build}

%files test
%license LICENSE.TXT
%{_bindir}/not
%{_bindir}/count
%{_bindir}/yaml-bench
%{_bindir}/lli-child-target
%{_bindir}/llvm-isel-fuzzer
%{_bindir}/llvm-opt-fuzzer

%files googletest
%license LICENSE.TXT
%{_datadir}/llvm/src/utils
%{_libdir}/libLLVMTestingSupport.a

%if 0%{?rhel}
%files toolset
%license LICENSE.TXT
%endif

%endif

%changelog
* Thu Jan 19 2023 Tom Stellard <tstellar@redhat.com> - 15.0.7-1
- 15.0.7 Release

* Mon Oct 31 2022 Tom Stellard <tstellar@redhat.com> - 15.0.0-2
- Re-enable debuginfo for ppc64le

* Tue Sep 06 2022 Nikita Popov <npopov@redhat.com> - 15.0.0-1
- Update to LLVM 15.0.0

* Mon Jun 27 2022 Tom Stellard <tstellar@redhat.com> - 14.0.6-1
- 14.0.6 Release

* Mon May 23 2022 Timm Bäder <tbaeder@redhat.com> - 14.0.0-3
- Build gold plugin on s390x as well

* Fri Apr 29 2022 Timm Bäder <tbaeder@redhat.com> - 14.0.0-2
- Remove llvm-cmake-devel package again

* Thu Apr 07 2022 Timm Bäder <tbaeder@redhat.com> - 14.0.0-1
- Update to 14.0.0

* Wed Feb 02 2022 Tom Stellard <tstellar@redhat.com> - 13.0.1-1
- 13.0.1 Release

* Sat Jan 29 2022 Tom Stellard <tstellar@redhat.com> - 13.0.0-4
- Rebuild with gcc fix from rhbz#2028609

* Thu Oct 21 2021 sguelton@redhat.com - 13.0.0-3
- Correctly set ldflags

* Wed Oct 20 2021 Tom Stellard <tstellar@redhat.com> - 13.0.0-2
- Disable failing test on s390x

* Thu Oct 14 2021 Tom Stellard <tstellar@redhat.com> - 13.0.0-1
- 13.0.0 Release

* Fri Jul 16 2021 sguelton@redhat.com - 12.0.1-1
- 12.0.1 release

* Fri Jul 02 2021 Tom Stellard <tstellar@redhat.com> - 12.0.0-2
- Stop installing lit tests

* Tue May 25 2021 sguelton@redhat.com - 12.0.0-1
- Remove obsolete patch

* Thu Oct 29 2020 sguelton@redhat.com - 11.0.0-2
- Remove obsolete patch

* Wed Sep 30 2020 sguelton@redhat.com - 11.0.0-1
- 11.0.1 final release

* Wed Sep 30 2020 sguelton@redhat.com - 11.0.0-0.6.rc2
- Restore default CI behavior wrt. number of threads

* Fri Sep 25 2020 sguelton@redhat.com - 11.0.0-0.5.rc2
- Fix test case depending on fs capability

* Fri Sep 25 2020 sguelton@redhat.com - 11.0.0-0.4.rc2
- Fix dependency on dsymutil.rst from CI

* Thu Sep 24 2020 sguelton@redhat.com - 11.0.0-0.3.rc2
- Fix test file generation

* Wed Sep 23 2020 sguelton@redhat.com - 11.0.0-0.2.rc2
- Remove runtime dep on libedit-devel

* Mon Sep 14 2020 sguelton@redhat.com - 11.0.0-0.1.rc2
- 11.0.1.rc2 Release

* Wed Aug 19 2020 Tom Stellard <tstellar@redhat.com> - 10.0.1-3
- Fix rust crash on ppc64le compiling firefox

* Fri Jul 31 2020 sguelton@redhat.com - 10.0.1-2
- Fix llvm-config alternative handling, see rhbz#1859996

* Fri Jul 24 2020 sguelton@redhat.com - 10.0.1-1
- 10.0.1 Release

* Wed Jun 24 2020 sguelton@redhat.com - 10.0.0-2
- Reproducible build of test.tar.gz, see rhbz#1820319

* Tue Apr 7 2020 sguelton@redhat.com - 10.0.0-1
- 10.0.0 Release

* Thu Feb 27 2020 Josh Stone <jistone@redhat.com> - 9.0.1-4
- Fix a codegen bug for Rust

* Fri Jan 17 2020 Tom Stellard <tstellar@redhat.com> - 9.0.1-3
- Add explicit Requires from sub-packages to llvm-libs

* Fri Jan 10 2020 Tom Stellard <tstellar@redhat.com> - 9.0.1-2
- Fix crash with kernel bpf self-tests

* Thu Dec 19 2019 tstellar@redhat.com - 9.0.1-1
- 9.0.1 Release

* Wed Oct 30 2019 Tom Stellard <tstellar@redhat.com> - 9.0.0-5
- Remove work-around for threading issue in gold

* Wed Oct 30 2019 Tom Stellard <tstellar@redhat.com> - 9.0.0-4
- Build libLLVM.so first to avoid OOM errors

* Tue Oct 01 2019 Tom Stellard <tstellar@redhat.com> - 9.0.0-3
- Adjust run-lit-tests script to better match in tree testing

* Mon Sep 30 2019 Tom Stellard <tstellar@redhat.com> - 9.0.0-2
- Limit number of build threads using -l option for ninja

* Thu Sep 26 2019 Tom Stellard <tstellar@redhat.com> - 9.0.0-1
- 9.0.0 Release

* Thu Aug 1 2019 sguelton@redhat.com - 8.0.1-1
- 8.0.1 release

* Tue Jul 2 2019 sguelton@redhat.com - 8.0.1-0.3.rc2
- Deactivate multithreading for gold plugin only to fix rhbz#1636479

* Mon Jun 17 2019 sguelton@redhat.com - 8.0.1-0.2.rc2
- Deactivate multithreading instead of patching to fix rhbz#1636479

* Thu Jun 13 2019 sguelton@redhat.com - 8.0.1-0.1.rc2
- 8.0.1rc2 Release

* Tue May 14 2019 sguelton@redhat.com - 8.0.0-3
- Disable threading in LTO

* Wed May 8 2019 sguelton@redhat.com - 8.0.0-2
- Fix conflicts between llvm-static = 8 and llvm-dev < 8 around LLVMStaticExports.cmake

* Thu May 2 2019 sguelton@redhat.com - 8.0.0-1
- 8.0.0 Release

* Fri Dec 14 2018 Tom Stellard <tstellar@redhat.com> - 7.0.1-1
- 7.0.1 Release

* Thu Dec 13 2018 Tom Stellard <tstellar@redhat.com> - 7.0.1-0.5.rc3
- Drop compat libs

* Wed Dec 12 2018 Tom Stellard <tstellar@redhat.com> - 7.0.1-0.4.rc3
- Fix ambiguous python shebangs

* Tue Dec 11 2018 Tom Stellard <tstellar@redhat.com> - 7.0.1-0.3.rc3
- Disable threading in thinLTO

* Tue Dec 11 2018 Tom Stellard <tstellar@redhat.com> - 7.0.1-0.2.rc3
- Update cmake options for compat build

* Mon Dec 10 2018 Tom Stellard <tstellar@redhat.com> - 7.0.1-0.1.rc3
- 7.0.1-rc3 Release

* Fri Dec 07 2018 Tom Stellard <tstellar@redhat.com> - 6.0.1-14
- Don't build llvm-test on i686

* Thu Dec 06 2018 Tom Stellard <tstellar@redhat.com> - 6.0.1-13
- Fix build when python2 is not present on system

* Tue Nov 06 2018 Tom Stellard <tstellar@redhat.com> - 6.0.1-12
- Fix multi-lib installation of llvm-devel

* Tue Oct 23 2018 Tom Stellard <tstellar@redhat.com> - 6.0.1-11
- Add sub-packages for testing

* Mon Oct 01 2018 Tom Stellard <tstellar@redhat.com> - 6.0.1-10
- Drop scl macros

* Tue Aug 28 2018 Tom Stellard <tstellar@redhat.com> - 6.0.1-9
- Drop libedit dependency

* Tue Aug 14 2018 Tom Stellard <tstellar@redhat.com> - 6.0.1-8
- Only enabled valgrind functionality on arches that support it

* Mon Aug 13 2018 Tom Stellard <tstellar@redhat.com> - 6.0.1-7
- BuildRequires: python3-devel

* Mon Aug 06 2018 Tom Stellard <tstellar@redhat.com> - 6.0.1-6
- Backport fixes for rhbz#1610053, rhbz#1562196, rhbz#1595996

* Mon Aug 06 2018 Tom Stellard <tstellar@redhat.com> - 6.0.1-5
- Fix ld.so.conf.d path in files list

* Sat Aug 04 2018 Tom Stellard <tstellar@redhat.com> - 6.0.1-4
- Fix ld.so.conf.d path

* Fri Aug 03 2018 Tom Stellard <tstellar@redhat.com> - 6.0.1-3
- Install ld.so.conf so llvm libs are in the library search path

* Wed Jul 25 2018 Tom Stellard <tstellar@redhat.com> - 6.0.1-2
- Re-enable doc package now that BREW-2381 is fixed

* Tue Jul 10 2018 Tom Stellard <tstellar@redhat.com> - 6.0.1-1
- 6.0.1 Release

* Mon Jun 04 2018 Tom Stellard <tstellar@redhat.com> - 5.0.1-13
- Limit build jobs on ppc64 to avoid OOM errors

* Sat Jun 02 2018 Tom Stellard <tstellar@redhat.com> - 5.0.1-12
- Switch to python3-sphinx

* Thu May 31 2018 Tom Stellard <tstellar@redhat.com> - 5.0.1-11
- Remove conditionals to enable building only the llvm-libs package, we don't
  needs these for module builds.

* Wed May 23 2018 Tom Stellard <tstellar@redhat.com> - 5.0.1-10
- Add BuildRequires: libstdc++-static
- Resolves: #1580785

* Wed Apr 04 2018 Tom Stellard <tstellar@redhat.com> - 5.0.1-9
- Add conditionals to enable building only the llvm-libs package

* Tue Apr 03 2018 Tom Stellard <tstellar@redhat.com> - 5.0.1-8
- Drop BuildRequires: libstdc++-static this package does not exist in RHEL8

* Tue Mar 20 2018 Tilmann Scheller <tschelle@redhat.com> - 5.0.1-7
- Backport fix for rhbz#1558226 from trunk

* Tue Mar 06 2018 Tilmann Scheller <tschelle@redhat.com> - 5.0.1-6
- Backport fix for rhbz#1550469 from trunk

* Thu Feb 22 2018 Tom Stellard <tstellar@redhat.com> - 5.0.1-5
- Backport some retpoline fixes

* Tue Feb 06 2018 Tom Stellard <tstellar@redhat.com> - 5.0.1-4
- Backport retpoline support

* Mon Jan 29 2018 Tom Stellard <tstellar@redhat.com> - 5.0.1-3
- Backport r315279 to fix an issue with rust

* Mon Jan 15 2018 Tom Stellard <tstellar@redhat.com> - 5.0.1-2
- Drop ExculdeArch: ppc64

* Mon Jan 08 2018 Tom Stellard <tstellar@redhat.com> - 5.0.1-1
- 5.0.1 Release

* Thu Jun 22 2017 Tom Stellard <tstellar@redhat.com> - 4.0.1-3
- Fix Requires for devel package again.

* Thu Jun 22 2017 Tom Stellard <tstellar@redhat.com> - 4.0.1-2
- Fix Requires for llvm-devel

* Tue Jun 20 2017 Tom Stellard <tstellar@redhat.com> - 4.0.1-1
- 4.0.1 Release

* Mon Jun 05 2017 Tom Stellard <tstellar@redhat.com> - 4.0.0-5
- Build for llvm-toolset-7 rename

* Mon May 01 2017 Tom Stellard <tstellar@redhat.com> - 4.0.0-4
- Remove multi-lib workarounds

* Fri Apr 28 2017 Tom Stellard <tstellar@redhat.com> - 4.0.0-3
- Fix build with llvm-toolset-4 scl

* Mon Apr 03 2017 Tom Stellard <tstellar@redhat.com> - 4.0.0-2
- Simplify spec with rpm macros.

* Thu Mar 23 2017 Tom Stellard <tstellar@redhat.com> - 4.0.0-1
- LLVM 4.0.0 Final Release

* Wed Mar 22 2017 tstellar@redhat.com - 3.9.1-6
- Fix %%postun sep for -devel package.

* Mon Mar 13 2017 Tom Stellard <tstellar@redhat.com> - 3.9.1-5
- Disable failing tests on ARM.

* Sun Mar 12 2017 Peter Robinson <pbrobinson@fedoraproject.org> 3.9.1-4
- Fix missing mask on relocation for aarch64 (rhbz 1429050)

* Wed Mar 01 2017 Dave Airlie <airlied@redhat.com> - 3.9.1-3
- revert upstream radeonsi breaking change.

* Thu Feb 23 2017 Josh Stone <jistone@redhat.com> - 3.9.1-2
- disable sphinx warnings-as-errors

* Fri Feb 10 2017 Orion Poplawski <orion@cora.nwra.com> - 3.9.1-1
- llvm 3.9.1

* Fri Feb 10 2017 Fedora Release Engineering <releng@fedoraproject.org> - 3.9.0-8
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Tue Nov 29 2016 Josh Stone <jistone@redhat.com> - 3.9.0-7
- Apply backports from rust-lang/llvm#55, #57

* Tue Nov 01 2016 Dave Airlie <airlied@gmail.com - 3.9.0-6
- rebuild for new arches

* Wed Oct 26 2016 Dave Airlie <airlied@redhat.com> - 3.9.0-5
- apply the patch from -4

* Wed Oct 26 2016 Dave Airlie <airlied@redhat.com> - 3.9.0-4
- add fix for lldb out-of-tree build

* Mon Oct 17 2016 Josh Stone <jistone@redhat.com> - 3.9.0-3
- Apply backports from rust-lang/llvm#47, #48, #53, #54

* Sat Oct 15 2016 Josh Stone <jistone@redhat.com> - 3.9.0-2
- Apply an InstCombine backport via rust-lang/llvm#51

* Wed Sep 07 2016 Dave Airlie <airlied@redhat.com> - 3.9.0-1
- llvm 3.9.0
- upstream moved where cmake files are packaged.
- upstream dropped CppBackend

* Wed Jul 13 2016 Adam Jackson <ajax@redhat.com> - 3.8.1-1
- llvm 3.8.1
- Add mips target
- Fix some shared library mispackaging

* Tue Jun 07 2016 Jan Vcelak <jvcelak@fedoraproject.org> - 3.8.0-2
- fix color support detection on terminal

* Thu Mar 10 2016 Dave Airlie <airlied@redhat.com> 3.8.0-1
- llvm 3.8.0 release

* Wed Mar 09 2016 Dan Horák <dan[at][danny.cz> 3.8.0-0.3
- install back memory consumption workaround for s390

* Thu Mar 03 2016 Dave Airlie <airlied@redhat.com> 3.8.0-0.2
- llvm 3.8.0 rc3 release

* Fri Feb 19 2016 Dave Airlie <airlied@redhat.com> 3.8.0-0.1
- llvm 3.8.0 rc2 release

* Tue Feb 16 2016 Dan Horák <dan[at][danny.cz> 3.7.1-7
- recognize s390 as SystemZ when configuring build

* Sat Feb 13 2016 Dave Airlie <airlied@redhat.com> 3.7.1-6
- export C++ API for mesa.

* Sat Feb 13 2016 Dave Airlie <airlied@redhat.com> 3.7.1-5
- reintroduce llvm-static, clang needs it currently.

* Fri Feb 12 2016 Dave Airlie <airlied@redhat.com> 3.7.1-4
- jump back to single llvm library, the split libs aren't working very well.

* Fri Feb 05 2016 Dave Airlie <airlied@redhat.com> 3.7.1-3
- add missing obsoletes (#1303497)

* Thu Feb 04 2016 Fedora Release Engineering <releng@fedoraproject.org> - 3.7.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Thu Jan 07 2016 Jan Vcelak <jvcelak@fedoraproject.org> 3.7.1-1
- new upstream release
- enable gold linker

* Wed Nov 04 2015 Jan Vcelak <jvcelak@fedoraproject.org> 3.7.0-100
- fix Requires for subpackages on the main package

* Tue Oct 06 2015 Jan Vcelak <jvcelak@fedoraproject.org> 3.7.0-100
- initial version using cmake build system
