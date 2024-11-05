%bcond_with snapshot_build

%if %{with snapshot_build}
# Unlock LLVM Snapshot LUA functions
%{llvm_sb}
%endif

# We are building with clang for faster/lower memory LTO builds.
# See https://docs.fedoraproject.org/en-US/packaging-guidelines/#_compiler_macros
%global toolchain clang

# Opt out of https://fedoraproject.org/wiki/Changes/fno-omit-frame-pointer
# https://bugzilla.redhat.com/show_bug.cgi?id=2158587
%undefine _include_frame_pointers

# Components enabled if supported by target architecture:
%define gold_arches %{ix86} x86_64 aarch64 %{power64} s390x
%ifarch %{gold_arches}
  %bcond_without gold
%else
  %bcond_with gold
%endif

%bcond_with compat_build
%bcond_without check

%ifarch %ix86
# Disable LTO on x86 in order to reduce memory consumption
%bcond_with lto_build
%else
%bcond_without lto_build
%endif

%global maj_ver 18
%global min_ver 1
%global patch_ver 8
#global rc_ver 4

%if %{with snapshot_build}
%undefine rc_ver
%global maj_ver %{llvm_snapshot_version_major}
%global min_ver %{llvm_snapshot_version_minor}
%global patch_ver %{llvm_snapshot_version_patch}
%endif

%global llvm_srcdir llvm-%{maj_ver}.%{min_ver}.%{patch_ver}%{?rc_ver:rc%{rc_ver}}.src
%global cmake_srcdir cmake-%{maj_ver}.%{min_ver}.%{patch_ver}%{?rc_ver:rc%{rc_ver}}.src
%global third_party_srcdir third-party-%{maj_ver}.%{min_ver}.%{patch_ver}%{?rc_ver:rc%{rc_ver}}.src

%if %{with compat_build}
%global pkg_name llvm%{maj_ver}
%global exec_suffix -%{maj_ver}
%global install_prefix %{_libdir}/%{name}
%global install_bindir %{install_prefix}/bin
%global install_includedir %{install_prefix}/include
%global install_libdir %{install_prefix}/lib

%global pkg_includedir %{_includedir}/%{name}
%global pkg_datadir %{install_prefix}/share
%else
%global pkg_name llvm
%global install_prefix /usr
%global install_bindir %{_bindir}
%global install_libdir %{_libdir}
%global install_includedir %{_includedir}
%global pkg_datadir %{_datadir}
%global exec_suffix %{nil}
%endif

%if 0%{?rhel}
%global targets_to_build "X86;AMDGPU;PowerPC;NVPTX;SystemZ;AArch64;ARM;Mips;BPF;WebAssembly"
%global experimental_targets_to_build ""
%else
%global targets_to_build "all"
%global experimental_targets_to_build "AVR"
%endif

%global build_install_prefix %{buildroot}%{install_prefix}

# Lower memory usage of dwz on s390x
%global _dwz_low_mem_die_limit_s390x 1
%global _dwz_max_die_limit_s390x 1000000

%global llvm_triple %{_target_platform}

# https://fedoraproject.org/wiki/Changes/PythonSafePath#Opting_out
# Don't add -P to Python shebangs
# The executable Python scripts in /usr/share/opt-viewer/ import each other
%undefine _py3_shebang_P

################################################################################
# OS Specific Configuration
################################################################################

########
# RHEL #
########
%if 0%{?rhel}
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
%endif

################################################################################
# Spec File
################################################################################


Name:		%{pkg_name}
Version:	%{maj_ver}.%{min_ver}.%{patch_ver}%{?rc_ver:~rc%{rc_ver}}%{?llvm_snapshot_version_suffix:~%{llvm_snapshot_version_suffix}}
Release:	3%{?dist}
Summary:	The Low Level Virtual Machine

License:	Apache-2.0 WITH LLVM-exception OR NCSA
URL:		http://llvm.org
%if %{with snapshot_build}
Source0:	%{llvm_snapshot_source_prefix}llvm-%{llvm_snapshot_yyyymmdd}.src.tar.xz
Source2:	%{llvm_snapshot_source_prefix}cmake-%{llvm_snapshot_yyyymmdd}.src.tar.xz
Source4:	%{llvm_snapshot_source_prefix}third-party-%{llvm_snapshot_yyyymmdd}.src.tar.xz
%{llvm_snapshot_extra_source_tags}
%else
Source0:	https://github.com/llvm/llvm-project/releases/download/llvmorg-%{maj_ver}.%{min_ver}.%{patch_ver}%{?rc_ver:-rc%{rc_ver}}/%{llvm_srcdir}.tar.xz
Source1:	https://github.com/llvm/llvm-project/releases/download/llvmorg-%{maj_ver}.%{min_ver}.%{patch_ver}%{?rc_ver:-rc%{rc_ver}}/%{llvm_srcdir}.tar.xz.sig
Source2:	https://github.com/llvm/llvm-project/releases/download/llvmorg-%{maj_ver}.%{min_ver}.%{patch_ver}%{?rc_ver:-rc%{rc_ver}}/%{cmake_srcdir}.tar.xz
Source3:	https://github.com/llvm/llvm-project/releases/download/llvmorg-%{maj_ver}.%{min_ver}.%{patch_ver}%{?rc_ver:-rc%{rc_ver}}/%{cmake_srcdir}.tar.xz.sig
Source4:	https://github.com/llvm/llvm-project/releases/download/llvmorg-%{maj_ver}.%{min_ver}.%{patch_ver}%{?rc_ver:-rc%{rc_ver}}/%{third_party_srcdir}.tar.xz
Source5:	https://github.com/llvm/llvm-project/releases/download/llvmorg-%{maj_ver}.%{min_ver}.%{patch_ver}%{?rc_ver:-rc%{rc_ver}}/%{third_party_srcdir}.tar.xz.sig
Source6:	release-keys.asc
%endif

# Backport with modifications from
# https://github.com/llvm/llvm-project/pull/99273
# Fixes RHEL-54336
Patch001:	99273.patch
# RHEL-specific patch to avoid unwanted python3-myst-parser dep
Patch101:	0101-Deactivate-markdown-doc.patch

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
%if %{undefined rhel}
BuildRequires:	python3-myst-parser
%endif
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
# The installed cmake files reference binaries from llvm-test, llvm-static, and
# llvm-gtest.  We tried in the past to split the cmake exports for these binaries
# out into separate files, so that llvm-devel would not need to Require these packages,
# but this caused bugs (rhbz#1773678) and forced us to carry two non-upstream
# patches.
Requires:	%{name}-static%{?_isa} = %{version}-%{release}
Requires:	%{name}-test%{?_isa} = %{version}-%{release}
Requires:	%{name}-googletest%{?_isa} = %{version}-%{release}


Requires(post):	/usr/sbin/alternatives
Requires(postun):	/usr/sbin/alternatives

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
Requires(post): /sbin/ldconfig
Requires(postun): /sbin/ldconfig

%description libs
Shared libraries for the LLVM compiler infrastructure.

%package static
Summary:	LLVM static libraries
Conflicts:	%{name}-devel < 8

Provides:	llvm-static(major) = %{maj_ver}

%description static
Static libraries for the LLVM compiler infrastructure.

%package cmake-utils
Summary: CMake utilities shared across LLVM subprojects

%description cmake-utils
CMake utilities shared across LLVM subprojects.
This is for internal use by LLVM packages only.

%package test
Summary:	LLVM regression tests
Requires:	%{name}%{?_isa} = %{version}-%{release}
Requires:	%{name}-libs%{?_isa} = %{version}-%{release}

Provides:	llvm-test(major) = %{maj_ver}

%description test
LLVM regression tests.

%package googletest
Summary: LLVM's modified googletest sources
# libllvm_gtest.a moved from llvm-static to llvm-googletest
Conflicts: %{name}-static < 17.0.0

%description googletest
LLVM's modified googletest sources.

%if 0%{?rhel}
%package toolset
Summary:	Package that installs llvm-toolset
Requires:	clang = %{version}
Requires:	llvm = %{version}

%description toolset
This is the main package for llvm-toolset.
%endif

%prep
%{gpgverify} --keyring='%{SOURCE6}' --signature='%{SOURCE1}' --data='%{SOURCE0}'
%{gpgverify} --keyring='%{SOURCE6}' --signature='%{SOURCE3}' --data='%{SOURCE2}'
%{gpgverify} --keyring='%{SOURCE6}' --signature='%{SOURCE5}' --data='%{SOURCE4}'
%setup -T -q -b 2 -n %{cmake_srcdir}
# TODO: It would be more elegant to set -DLLVM_COMMON_CMAKE_UTILS=%{_builddir}/%{cmake_srcdir},
# but this is not a CACHED variable, so we can't actually set it externally :(
cd ..
mv %{cmake_srcdir} cmake
%setup -T -q -b 4 -n %{third_party_srcdir}
cd ..
mv %{third_party_srcdir} third-party

%setup -T -q -b 0 -n %{llvm_srcdir}
%autopatch -M%{?!rhel:100}%{?rhel:200} -p2

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

%if %{without lto_build}
%global _lto_cflags %nil
%endif

%ifarch s390 s390x %ix86
# Decrease debuginfo verbosity to reduce memory consumption during final library linking
%global optflags %(echo %{optflags} | sed 's/-g /-g1 /')
%endif

# Copy CFLAGS into ASMFLAGS, so -fcf-protection is used when compiling assembly files.
export ASMFLAGS="%{build_cflags}"

# force off shared libs as cmake macros turns it on.
# TODO: Disable LLVM_UNREACHABLE_OPTIMIZE.
%cmake	-G Ninja \
	-DBUILD_SHARED_LIBS:BOOL=OFF \
	-DLLVM_PARALLEL_LINK_JOBS=1 \
	-DCMAKE_BUILD_TYPE=RelWithDebInfo \
	-DCMAKE_SKIP_RPATH:BOOL=ON \
%ifarch s390 %ix86
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
	-DLLVM_INSTALL_GTEST:BOOL=ON \
	-DLLVM_LIT_ARGS=-v \
	\
	-DLLVM_INCLUDE_EXAMPLES:BOOL=ON \
	-DLLVM_BUILD_EXAMPLES:BOOL=OFF \
	\
	-DLLVM_INCLUDE_UTILS:BOOL=ON \
	-DLLVM_INSTALL_UTILS:BOOL=ON \
	-DLLVM_UTILS_INSTALL_DIR:PATH=bin \
	-DLLVM_TOOLS_INSTALL_DIR:PATH=bin \
	\
	-DLLVM_INCLUDE_DOCS:BOOL=ON \
	-DLLVM_BUILD_DOCS:BOOL=ON \
	-DLLVM_ENABLE_SPHINX:BOOL=ON \
	-DLLVM_ENABLE_DOXYGEN:BOOL=OFF \
	\
%if %{with snapshot_build}
	-DLLVM_VERSION_SUFFIX="%{llvm_snapshot_version_suffix}" \
%else
	-DLLVM_VERSION_SUFFIX='' \
%endif
	-DLLVM_UNREACHABLE_OPTIMIZE:BOOL=ON \
	-DLLVM_BUILD_LLVM_DYLIB:BOOL=ON \
	-DLLVM_LINK_LLVM_DYLIB:BOOL=ON \
	-DLLVM_BUILD_EXTERNAL_COMPILER_RT:BOOL=ON \
	-DLLVM_INSTALL_TOOLCHAIN_ONLY:BOOL=OFF \
	-DLLVM_DEFAULT_TARGET_TRIPLE=%{llvm_triple} \
	-DSPHINX_WARNINGS_AS_ERRORS=OFF \
	-DCMAKE_INSTALL_PREFIX=%{install_prefix} \
	-DLLVM_INSTALL_SPHINX_HTML_DIR=%{_pkgdocdir}/html \
	-DSPHINX_EXECUTABLE=/usr/bin/sphinx-build-3 \
	-DLLVM_INCLUDE_BENCHMARKS=OFF \
%if %{with lto_build}
	-DLLVM_UNITTEST_LINK_FLAGS="-Wl,-plugin-opt=O0" \
%endif
%ifarch x86_64
	-DCMAKE_SHARED_LINKER_FLAGS="$LDFLAGS -Wl,-z,cet-report=error"
%endif

# Build libLLVM.so first.  This ensures that when libLLVM.so is linking, there
# are no other compile jobs running.  This will help reduce OOM errors on the
# builders without having to artificially limit the number of concurrent jobs.
%cmake_build --target LLVM
%cmake_build

%install
%cmake_install

mkdir -p %{buildroot}/%{_bindir}

# Install binaries needed for lit tests
%global test_binaries llvm-isel-fuzzer llvm-opt-fuzzer

for f in %{test_binaries}
do
    install -m 0755 %{_vpath_builddir}/bin/$f %{buildroot}%{install_bindir}
done

# Remove testing of update utility tools
rm -rf test/tools/UpdateTestChecks

# Install libraries needed for unittests
%if %{without compat_build}
%global build_libdir %{_vpath_builddir}/%{_lib}
%else
%global build_libdir %{_vpath_builddir}/lib
%endif

install %{build_libdir}/libLLVMTestingSupport.a %{buildroot}%{install_libdir}
install %{build_libdir}/libLLVMTestingAnnotations.a %{buildroot}%{install_libdir}

# Fix multi-lib
%multilib_fix_c_header --file %{install_includedir}/llvm/Config/llvm-config.h

%if %{without compat_build}

# Fix some man pages
ln -s llvm-config.1 %{buildroot}%{_mandir}/man1/llvm-config%{exec_suffix}-%{__isa_bits}.1

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

# Create ld.so.conf.d entry
mkdir -p %{buildroot}/etc/ld.so.conf.d
cat >> %{buildroot}/etc/ld.so.conf.d/%{name}-%{_arch}.conf << EOF
%{install_libdir}
EOF

# Add version suffix to man pages and move them to mandir.
mkdir -p %{buildroot}/%{_mandir}/man1
for f in %{build_install_prefix}/share/man/man1/*; do
  filename=`basename $f | cut -f 1 -d '.'`
  mv $f %{buildroot}%{_mandir}/man1/$filename%{exec_suffix}.1
done

%endif

# llvm-config special casing. llvm-config is managed by update-alternatives.
# the original file must remain available for compatibility with the CMake
# infrastructure. Without compat, cmake points to the symlink, with compat it
# points to the original file.

%if %{without compat_build}

mv %{buildroot}/%{install_bindir}/llvm-config %{buildroot}/%{install_bindir}/llvm-config%{exec_suffix}-%{__isa_bits}
# We still maintain a versionned symlink for consistency across llvm versions.
# This is specific to the non-compat build and matches the exec prefix for
# compat builds. An isa-agnostic versionned symlink is also maintained in the (un)install
# steps.
(cd %{buildroot}/%{install_bindir} ; ln -s llvm-config%{exec_suffix}-%{__isa_bits} llvm-config-%{maj_ver}-%{__isa_bits} )
# ghost presence
touch %{buildroot}%{_bindir}/llvm-config-%{maj_ver}

%else

rm %{buildroot}%{_bindir}/llvm-config%{exec_suffix}
(cd %{buildroot}/%{install_bindir} ; ln -s llvm-config llvm-config%{exec_suffix}-%{__isa_bits} )

%endif

# ghost presence
touch %{buildroot}%{_bindir}/llvm-config%{exec_suffix}

mkdir -p %{buildroot}%{pkg_datadir}/llvm/cmake
cp -Rv ../cmake/* %{buildroot}%{pkg_datadir}/llvm/cmake

%check
# non reproducible errors
rm test/tools/dsymutil/X86/swift-interface.test

%if %{with check}
# FIXME: use %%cmake_build instead of %%__ninja
LD_LIBRARY_PATH=%{buildroot}/%{install_libdir}  %{__ninja} check-all -C %{_vpath_builddir}
%endif

%if %{with compat_build}
# Packages that install files in /etc/ld.so.conf have to manually run
# ldconfig.
# See https://bugzilla.redhat.com/show_bug.cgi?id=2001328 and
# https://docs.fedoraproject.org/en-US/packaging-guidelines/Scriptlets/#_linker_configuration_files
%post -p /sbin/ldconfig libs
%postun -p /sbin/ldconfig libs
%endif

%post devel
/usr/sbin/update-alternatives --install %{_bindir}/llvm-config%{exec_suffix} llvm-config%{exec_suffix} %{install_bindir}/llvm-config%{exec_suffix}-%{__isa_bits} %{__isa_bits}
%if %{without compat_build}
/usr/sbin/update-alternatives --install %{_bindir}/llvm-config-%{maj_ver} llvm-config-%{maj_ver} %{install_bindir}/llvm-config%{exec_suffix}-%{__isa_bits} %{__isa_bits}

# During the upgrade from LLVM 16 (F38) to LLVM 17 (F39), we found out the
# main llvm-devel package was leaving entries in the alternatives system.
# Try to remove them now.
for v in 14 15 16; do
  if [[ -e %{_bindir}/llvm-config-$v
		&& "x$(%{_bindir}/llvm-config-$v --version | awk -F . '{ print $1 }')" != "x$v" ]]; then
    /usr/sbin/update-alternatives --remove llvm-config-$v %{install_bindir}/llvm-config%{exec_suffix}-%{__isa_bits}
  fi
done
%endif

%postun devel
if [ $1 -eq 0 ]; then
  /usr/sbin/update-alternatives --remove llvm-config%{exec_suffix} %{install_bindir}/llvm-config%{exec_suffix}-%{__isa_bits}
fi
%if %{without compat_build}
# When upgrading between minor versions (i.e. from x.y.1 to x.y.2), we must
# not remove the alternative.
# However, during a major version upgrade (i.e. from 16.x.y to 17.z.w), the
# alternative must be removed in order to give priority to a newly installed
# compat package.
if [[ $1 -eq 0
	  || "x$(%{_bindir}/llvm-config-%{maj_ver} --version | awk -F . '{ print $1 }')" != "x%{maj_ver}" ]]; then
  /usr/sbin/update-alternatives --remove llvm-config-%{maj_ver} %{install_bindir}/llvm-config%{exec_suffix}-%{__isa_bits}
fi
%endif

%files
%license LICENSE.TXT
%exclude %{_mandir}/man1/llvm-config*
%{_mandir}/man1/*
%{install_bindir}/*
%if %{with compat_build}
# This is for all the binaries with the version suffix.
%{_bindir}/*%{exec_suffix}
%endif

%exclude %{_bindir}/llvm-config%{exec_suffix}
%exclude %{install_bindir}/llvm-config%{exec_suffix}-%{__isa_bits}

%exclude %{_bindir}/llvm-config-%{maj_ver}
%exclude %{install_bindir}/llvm-config-%{maj_ver}-%{__isa_bits}
%exclude %{install_bindir}/not
%exclude %{install_bindir}/count
%exclude %{install_bindir}/yaml-bench
%exclude %{install_bindir}/lli-child-target
%exclude %{install_bindir}/llvm-isel-fuzzer
%exclude %{install_bindir}/llvm-opt-fuzzer
%{pkg_datadir}/opt-viewer

%files libs
%license LICENSE.TXT
%{install_libdir}/libLLVM-%{maj_ver}%{?llvm_snapshot_version_suffix:%{llvm_snapshot_version_suffix}}.so
%if %{with gold}
%{install_libdir}/LLVMgold.so
%if %{without compat_build}
%{_libdir}/bfd-plugins/LLVMgold.so
%endif
%endif
%{install_libdir}/libLLVM-%{maj_ver}.so
%{install_libdir}/libLLVM.so.%{maj_ver}.%{min_ver}
%{install_libdir}/libLTO.so*
%{install_libdir}/libRemarks.so*
%if %{with compat_build}
%config(noreplace) /etc/ld.so.conf.d/%{name}-%{_arch}.conf
%endif

%files devel
%license LICENSE.TXT

%ghost %{_bindir}/llvm-config%{exec_suffix}
%{install_bindir}/llvm-config%{exec_suffix}-%{__isa_bits}
%{_mandir}/man1/llvm-config*

%{install_includedir}/llvm
%{install_includedir}/llvm-c
%{install_libdir}/libLLVM.so
%{install_libdir}/cmake/llvm
%{install_bindir}/llvm-config-%{maj_ver}-%{__isa_bits}
%ghost %{_bindir}/llvm-config-%{maj_ver}

%files doc
%license LICENSE.TXT
%doc %{_pkgdocdir}/html

%files static
%license LICENSE.TXT
%{install_libdir}/*.a
%exclude %{install_libdir}/libLLVMTestingSupport.a
%exclude %{install_libdir}/libLLVMTestingAnnotations.a
%exclude %{install_libdir}/libllvm_gtest.a
%exclude %{install_libdir}/libllvm_gtest_main.a

%files cmake-utils
%license LICENSE.TXT
%{pkg_datadir}/llvm/cmake

%files test
%license LICENSE.TXT
%{install_bindir}/not
%{install_bindir}/count
%{install_bindir}/yaml-bench
%{install_bindir}/lli-child-target
%{install_bindir}/llvm-isel-fuzzer
%{install_bindir}/llvm-opt-fuzzer

%files googletest
%license LICENSE.TXT
%{install_libdir}/libLLVMTestingSupport.a
%{install_libdir}/libLLVMTestingAnnotations.a
%{install_libdir}/libllvm_gtest.a
%{install_libdir}/libllvm_gtest_main.a
%{install_includedir}/llvm-gtest
%{install_includedir}/llvm-gmock

%if 0%{?rhel}
%files toolset
%license LICENSE.TXT
%endif

%changelog
* Fri Oct 18 2024 Tom Stellard <tstellar@redhat.com> - 18.1.8-3
- Remove stray fi from postun scriptlet

* Fri Oct 18 2024 Tulio Magno Quites Machado Filho <tuliom@redhat.com> - 18.1.8-2
- Workaround for GFX11.5 export priority

* Fri Oct 18 2024 Tom Stellard <tstellar@redhat.com> - 18.1.8-1
- 18.1.8 Release

* Fri Oct 18 2024 Tom Stellard <tstellar@redhat.com> - 18.1.2-1
- 18.1.2 Release

* Wed Jul 17 2024 Tom Stellard <tstellar@redhat.com> - 17.0.6-3
- Backport fix for RHEL-49522

* Fri Feb 02 2024 Nikita Popov <npopov@redhat.com> - 17.0.6-2
- Fix crash with -fzero-call-used-regs (RHEL-23865)

* Wed Nov 29 2023 Nikita Popov <npopov@redhat.com> - 17.0.6-1
- Update to LLVM 17.0.6

* Mon Oct 23 2023 Nikita Popov <npopov@redhat.com> - 17.0.2-2
- Add Conflicts to llvm-googletest

* Wed Oct 04 2023 Nikita Popov <npopov@redhat.com> - 17.0.2-1
- Update to LLVM 17.0.2

* Thu Aug 03 2023 Tulio Magno Quites Machado Filho <tuliom@redhat.com> - 16.0.6-3
- Fix rhbz #2228944

* Wed Jul 19 2023 Tulio Magno Quites Machado Filho <tuliom@redhat.com> - 16.0.6-2
- Improve error messages for unsupported relocs on s390x (rhbz#2216906)
- Disable LLVM_UNREACHABLE_OPTIMIZE

* Sat Jun 17 2023 Tom Stellard <tstellar@redhat.com> - 16.0.6-1
- 16.0.6 Release

* Wed Apr 05 2023 Timm Bäder <tbaeder@redhat.com> - 16.0.0-1
- 16.0.0 Release

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
