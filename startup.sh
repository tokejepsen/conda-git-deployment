# Get parent directory
parent_path="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Linux environment
echo "OS is Linux"

if [ ! -f "$parent_path"/linux/miniconda.sh ]; then
  echo "Downloading miniconda..."
  mkdir -p "$parent_path"/linux
  wget -O "$parent_path"/linux/miniconda.sh http://repo.continuum.io/miniconda/Miniconda-latest-Linux-x86_64.sh
fi

if [ ! -d "$parent_path"/linux/miniconda ]; then
  echo "Installing miniconda..."
  bash "$parent_path"/linux/miniconda.sh -b -p "$parent_path"/linux/miniconda
fi

export PATH="$parent_path"/linux/miniconda/bin:$PATH
export PYTHONPATH="$parent_path"/linux/miniconda/lib/python2.7/site-packages:$PYTHONPATH

python "$parent_path"/conda_git_deployment/update.py
