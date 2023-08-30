# vim:ft=spec

%define file_prefix M4_FILE_PREFIX
%define file_ext M4_FILE_EXT

%define file_version M4_FILE_VERSION
%define file_release_tag %{nil}M4_FILE_RELEASE_TAG
%define file_release_number M4_FILE_RELEASE_NUMBER
%define file_build_number M4_FILE_BUILD_NUMBER
%define file_commit_ref M4_FILE_COMMIT_REF

Name:           python-dpres-specification-migrator
Version:        %{file_version}
Release:        %{file_release_number}%{file_release_tag}.%{file_build_number}.git%{file_commit_ref}%{?dist}
Summary:        Tools for migrating information packages to newer versions
License:        LGPLv3+
URL:            https://digitalpreservation.fi
Source0:        %{file_prefix}-v%{file_version}%{?file_release_tag}-%{file_build_number}-g%{file_commit_ref}.%{file_ext}
BuildArch:      noarch

BuildRequires:  python3-devel
BuildRequires:  pyproject-rpm-macros
BuildRequires:  %{py3_dist pip}
BuildRequires:  %{py3_dist setuptools}
BuildRequires:  %{py3_dist wheel}

%global _description %{expand:
Tools for migrating information packages (SIPs and DIPs) to newer versions of
the specifications for the Finnish National Digital Preservation Services.
}

%description %_description

%package -n python3-dpres-specification-migrator
Summary: %{summary}
Requires: %{py3_dist xml-helpers}
Requires: %{py3_dist mets}
Requires: %{py3_dist premis}
%description -n python3-dpres-specification-migrator %_description

%prep
%autosetup -n %{file_prefix}-v%{file_version}%{?file_release_tag}-%{file_build_number}-g%{file_commit_ref}

%build
%pyproject_wheel

%install
%pyproject_install
%pyproject_save_files dpres_specification_migrator

cp -a %{buildroot}%{_bindir}/transform-mets %{buildroot}%{_bindir}/transform-mets-3

%files -n python3-dpres-specification-migrator -f %{pyproject_files}
%license LICENSE
%doc README.rst
%{_bindir}/transform-mets*

# TODO: For now changelog must be last, because it is generated automatically
# from git log command. Appending should be fixed to happen only after %changelog macro
%changelog
