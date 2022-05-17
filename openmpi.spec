Name:           openmpi
Version:        4.0.4
Release:        1
Summary:        Open Message Passing Interface
License:        BSD and MIT and Romio
URL:            http://www.open-mpi.org/
Source0:        https://download.open-mpi.org/release/open-mpi/v4.0/openmpi-%{version}.tar.bz2
Source1:        openmpi.module.in
Source2:        openmpi.pth.py3
Source3:        macros.openmpi

# Add OPAL patch to enable riscv64
# http://fedora.riscv.rocks:3000/rpms/openmpi/commit/14627af2cb42a8172d290a76e3c287c50109ad25
# Thu Jul 02 2020 David Abdurachmanov <david.abdurachmanov@sifive.com> - 4.0.4-1.0.riscv64
Patch1:        openmpi-4.0.1-riscv64.patch

BuildRequires:      gcc-c++, gcc-gfortran
BuildRequires:      valgrind-devel, hwloc-devel, java-devel, libfabric-devel, papi-devel
BuildRequires:      libibverbs-devel >= 1.1.3, opensm-devel > 3.3.0
BuildRequires:      librdmacm-devel, rdma-core-devel, pmix-devel, libevent-devel
BuildRequires:      hwloc-gui chrpath
BuildRequires:      perl-generators, perl-interpreter, perl(Getopt::Long)
BuildRequires:      python3-devel, zlib-devel
%bcond_with ucx
%if %{with ucx}
BuildRequires:   ucx-devel
%endif
%ifarch x86_64
BuildRequires:      infinipath-psm-devel, libpsm2-devel
%endif
%ifarch riscv64
BuildRequires:      autoconf automake libtool gettext
%endif

Provides:           mpi, %{name}-java
Requires:           environment(modules), openssh-clients
Provides:           bundled(libevent) = 2.0.22
Requires:           java-headless
Obsoletes:          %{name}-java

%description
The Open MPI Project is an open source Message Passing Interface
implementation that is developed and maintained by a consortium
of academic, research, and industry partners. Open MPI is
therefore able to combine the expertise, technologies, and
resources from all across the High Performance Computing
community in order to build the best MPI library available.

%ifarch aarch64
%global name_all openmpi-aarch64
%else
%global name_all openmpi-x86_64
%endif
%ifarch riscv64
%global name_all openmpi-%{_arch}
%endif

%package devel
Summary:    Development files for openmpi
Requires:   %{name} = %{version}-%{release}, gcc-gfortran
Provides:   mpi-devel
Requires:   java-devel
Provides:   %{name}-java-devel
Obsoletes:  %{name}-java-devel

%description devel
This contains dynamic libraries and header files for the developing of openmpi.

%package -n python3-openmpi
Summary:    openmpi python3 interface
Requires:   %{name} = %{version}-%{release}

%description -n python3-openmpi
openmpi python3 interface

%package        help
Summary:        Including man files for openmpi
Requires:       man

%description    help
This contains man files for the using of openmpi.

%prep
%autosetup -n openmpi-%{version} -p1

%ifarch riscv64
# autogen --> autoreconf to find newer 'alocal' & etc.
./autogen.pl --force
# Update config.* scripts to get RISC-V (riscv64) support
for f in $(find . -name config.guess); do
	cp -v -f /usr/lib/rpm/openEuler/config.guess "$f"
done
for f in $(find . -name config.sub); do
	cp -v -f /usr/lib/rpm/openEuler/config.sub "$f"
done
%endif

%build
./configure --prefix=%{_libdir}/%{name} \
            --includedir=%{_includedir}/%{name_all} \
            --sysconfdir=%{_sysconfdir}/%{name_all} \
            --disable-silent-rules \
            --enable-builtin-atomics \
            --enable-memchecker \
            --enable-mpi-thread-multiple \
            --enable-mpi-cxx \
            --enable-mpi-java \
            --with-sge \
            --with-valgrind \
            --with-hwloc=/usr \
            --mandir=%{_mandir}/%{name_all} \
            --with-libevent=external \
            --with-pmix=external \
            CFLAGS="$RPM_OPT_FLAGS" \
            CXXFLAGS="$RPM_OPT_FLAGS" \
            FC=gfortran \
            FCFLAGS="$RPM_OPT_FLAGS" \
	    LDFLAGS="-Wl,-z,now"

%make_build V=1

%install
%make_install
find %{buildroot}%{_libdir}/%{name}/lib -name \*.la -delete
find %{buildroot}%{_mandir}/%{name_all} -type f -exec gzip -9 {} \;
ln -s mpicc.1.gz %{buildroot}%{_mandir}/%{name_all}/man1/mpiCC.1.gz
rm %{buildroot}%{_mandir}/%{name_all}/man1/mpiCC.1
mkdir %{buildroot}%{_mandir}/%{name_all}/man{2,4,5,6,8,9,n}

mkdir -p %{buildroot}%{_datadir}/modulefiles/mpi
sed 's#@LIBDIR@#%{_libdir}/%{name}#;
     s#@ETCDIR@#%{_sysconfdir}/%{name_all}#;
     s#@FMODDIR@#%{_fmoddir}/%{name}#;
     s#@INCDIR@#%{_includedir}/%{name_all}#;
     s#@MANDIR@#%{_mandir}/%{name_all}#;
     s#@PY3SITEARCH@#%{python3_sitearch}/%{name}#;
     s#@COMPILER@#openmpi-%{_arch}#;
     s#@SUFFIX@#_openmpi#' \
     <%{SOURCE1} \
     >%{buildroot}%{_datadir}/modulefiles/mpi/%{name_all}

install -Dpm 644 %{SOURCE3} %{buildroot}/%{rpmmacrodir}/macros.%{name_all}

install -d %{buildroot}%{_fmoddir}/%{name}
for mod in %{buildroot}%{_libdir}/%{name}/lib/*.mod
do
  modname=$(basename $mod)
  ln -s ../../../%{name}/lib/${modname} %{buildroot}/%{_fmoddir}/%{name}/
done

install -d %{buildroot}%{_libdir}/pkgconfig
pushd %{buildroot}%{_libdir}/pkgconfig
ln -s ../%{name}/lib/pkgconfig/*.pc .
popd

sed -i -e s/-ldl// -e s/-lhwloc// \
  %{buildroot}%{_libdir}/%{name}/share/%{name}/*-wrapper-data.txt

install -d %{buildroot}/%{python3_sitearch}/%{name}
install -pDm0644 %{SOURCE2} %{buildroot}/%{python3_sitearch}/openmpi.pth

file `find %{buildroot}%{_libdir}/openmpi/bin  -type f` | grep -w ELF | awk -F : '{print $1}' |xargs chrpath -d
file `find %{buildroot}%{_libdir}/openmpi/lib  -type f` | grep -w ELF | awk -F : '{print $1}' |xargs chrpath -d

mkdir -p %{buildroot}/etc/ld.so.conf.d
echo "%{_libdir}/openmpi/lib" > %{buildroot}/etc/ld.so.conf.d/%{name}-%{_arch}.conf


%post
/sbin/ldconfig

%postun
/sbin/ldconfig



%check
make check

%files
%license LICENSE
%dir %{_libdir}/%{name}
%dir %{_sysconfdir}/%{name_all}
%dir %{_libdir}/%{name}/bin
%dir %{_libdir}/%{name}/lib
%dir %{_libdir}/%{name}/lib/openmpi
%dir %{_mandir}/%{name_all}
%dir %{_mandir}/%{name_all}/man*
%dir %{_libdir}/%{name}/share
%dir %{_libdir}/%{name}/share/openmpi
%config(noreplace) %{_sysconfdir}/%{name_all}/*
%config(noreplace) /etc/ld.so.conf.d/*
%{_datadir}/modulefiles/mpi/
%{_libdir}/%{name}/bin/mpiexec
%{_libdir}/%{name}/bin/mpirun
%{_libdir}/%{name}/bin/ompi*
%{_libdir}/%{name}/bin/orte-*
%{_libdir}/%{name}/bin/orted
%{_libdir}/%{name}/bin/orterun
%if %{with ucx}
%{_libdir}/%{name}/bin/oshmem_info
%{_libdir}/%{name}/bin/oshrun
%{_libdir}/%{name}/bin/shmemrun
%endif
%{_libdir}/%{name}/lib/*.so.*
%{_libdir}/%{name}/lib/openmpi/*
%{_libdir}/%{name}/lib/mpi.jar
%{_libdir}/%{name}/share/openmpi/help*.txt
%{_libdir}/%{name}/share/openmpi/amca-param-sets
%{_libdir}/%{name}/share/openmpi/mca-btl-openib-device-params.ini


%files devel
%dir %{_includedir}/%{name_all}
%{_includedir}/%{name_all}/*
%{_libdir}/%{name}/share/doc/
%{_libdir}/%{name}/bin/mpi[cCf]*
%{_libdir}/%{name}/bin/opal*
%{_libdir}/%{name}/bin/orte[cCf]*
%if %{with ucx}
%{_libdir}/%{name}/bin/osh[cCf]*
%{_libdir}/%{name}/bin/shmem[cCf]*
%endif
%{_libdir}/%{name}/bin/mpijava*
%{_libdir}/%{name}/bin/profile2mat.pl
%{_libdir}/%{name}/bin/aggregate_profile.pl
%{_libdir}/%{name}/lib/*.so
%{_libdir}/%{name}/lib/*.mod
%{_libdir}/%{name}/lib/pkgconfig/
%{_libdir}/%{name}/share/openmpi/*-wrapper-data.txt
%{_libdir}/%{name}/share/openmpi/openmpi-valgrind.supp
%{_libdir}/pkgconfig/*.pc
%{_fmoddir}/%{name}/
%{rpmmacrodir}/macros.%{name_all}

%files -n python3-openmpi
%dir %{python3_sitearch}/%{name}
%{python3_sitearch}/openmpi.pth

%files help
%{_mandir}/%{name_all}/man*/*

%changelog
* Mon May 16 2022 zxs-un <opensun@yeah.net> - 4.0.4-1
- upgrade to 4.0.4 and add support for riscv64 using OPAL patch from Fedora by David Abdurachmanov

* Thu Sep 9 2021 Pengju Jiang <jiangpengju2@huawei.com> - 2.1.1-20
- solve the strip and rpath problem of safe conversion

* Mon Nov 2 2020 wangxiao <wangxiao65@huawei.com> - 2.1.1-19
- delete unnessary file

* Wed Oct 21 2020 wangxiao <wangxiao65@huawei.com> - 2.1.1-18
- drop python2 subpackage

* Thu Sep 10 2020 Guoshuai Sun <sunguoshuai@huawei.com> - 2.1.1-17
- As rpm-mpi-hooks is not in buildrequire,we shouldn't pull it in devel packages

* Sat Jun 20 2020 Senlin Xia <xiasenlin1@huawei.com> - 2.1.1-16
- remove unnecessary buildrequire: rpm-mpi-hooks

* Tue Nov 26 2019 openEuler Buildteam <buildteam@openeuler.org> - 2-1.1-15
- Package init
