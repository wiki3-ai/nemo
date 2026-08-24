"""Entry point used by Jupyter to launch the Nemo kernel process."""

from nemo_kernel.kernel import NemoKernel
from ipykernel.kernelapp import IPKernelApp

if __name__ == "__main__":
    IPKernelApp.launch_instance(kernel_class=NemoKernel)
