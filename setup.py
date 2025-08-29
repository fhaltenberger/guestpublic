from setuptools import setup, find_packages

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name="guest",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    entry_points="""
        [console_scripts]
        guest=cli:cli
    """,
    py_modules=['cli', 'cli_authenticate', 'cli_send_qasm_file', 'cli_userinfo', "cli_qudi_commands", "cli_scheduling"],
) 