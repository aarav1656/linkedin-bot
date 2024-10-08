from setuptools import setup, find_packages

def read_requirements(file):
    with open(file) as f:
        return f.read().splitlines()

requirements = read_requirements("requirements.txt")

setup(
    name='PIS',
    version='1.0.0',  

    # Project description
    description='Linkedin Post Automation system',

    # Author information
    author='Aarav raj',
    author_email='aarav@exponentium.xyz',

    # Project URL
    url='https://github.com/aarav1656/Linkedin_Automation_with_Generative_AI.git',

    # Packages to be included in the distribution
    packages=["psi"],

    install_requires= ['openai', 'regex', 'requests', 'beautifulsoup4'],

    # Other metadata such as license, classifiers, etc.
    license='MIT',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
)
