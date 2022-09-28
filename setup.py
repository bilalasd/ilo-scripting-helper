import setuptools
import versioneer


with open("README.md", "r") as fh:
    long_description = fh.read()
with open("requirements.txt", "r") as fh:
    requirements = [line.strip() for line in fh]

setuptools.setup(
    name="ilo-scripting-helper",
    version=versioneer.get_version(),
    author="Muhammad Balagamwala",
    author_email="muhammadb@hpe.com",
    description="A Python library to provide useful function for scripting for iLO",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=requirements,
    cmdclass=versioneer.get_cmdclass(),
)
