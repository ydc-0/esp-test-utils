import sys


def main() -> None:
    """main function, show python version and module version"""
    print(f'Current python version: {sys.version}')
    assert sys.version_info.major == 3, 'Only support python3'
    if sys.version_info.minor < 8:
        import pkg_resources

        package_ver = pkg_resources.get_distribution('esptest').version
    else:
        from importlib.metadata import version

        package_ver = version('esptest')
    print(f'Installed esptest version: {package_ver}')


if __name__ == '__main__':
    main()
