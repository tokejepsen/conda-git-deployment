parent_path=$( cd "$(dirname "${BASH_SOURCE}")" ; pwd -P )

# Linux environment
echo "OS is Linux"
install_dir="$parent_path"/linux/miniconda

if [ ! -d "$install_dir" ]; then
  echo "Installing miniconda..."
  mkdir -p "$parent_path"/linux
  wget -O "$parent_path"/linux/miniconda.sh http://repo.continuum.io/miniconda/Miniconda-latest-Linux-x86_64.sh
  bash "$parent_path"/linux/miniconda.sh -b -p "$install_dir"
fi

export PATH="$install_dir"/bin:$PATH
export PYTHONPATH="$install_dir"/lib/python2.7/site-packages:$PYTHONPATH

python "$parent_path"/conda_git_deployment/update.py
