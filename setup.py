from setuptools import setup, find_packages

setup(
    name="mk8cv",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "opencv-python",
        "numpy",
        "redis",
        # Add other dependencies here
    ],
    extras_require={
        "dev": [
            "pytest",
            "flake8",
            # Add other development dependencies here
        ],
    },
    entry_points={
        "console_scripts": [
            "mk8cv=mk8cv.main:main",
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="A computer vision pipeline for Mario Kart 8",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/shingkai/MarioKart8CV",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
    ],
)
