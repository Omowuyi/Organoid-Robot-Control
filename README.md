# Organoid-Robot-Control
*This is code accompanying the publication*

Molokanova E. _et al._ **Graphene Optoelectronics for Non-Genetic Neuromodulation in Disease Modeling, Stem Cell Maturation, and Biohybrid Robotics** (2025)

## Installation

* Download and install [Anaconda](https://anaconda.com/download)
    * For Windows:
        * Double-click the downloaded installer file
        * Click "Next" to proceed through the installation wizard.
        * Accept the license agreement by clicking "I Agree".
        * Choose whether to install Anaconda for all users or just the current user.
        * Select your preferred installation location (default is recommended). 
    * For Mac:
        * Open the Terminal application on your Mac
        * Navigate to the installation directory of Anaconda
        * If you chose to install Anaconda for all users, you may need to use **sudo**
        * Once Anaconda is installed, the installer will prompt you to initialize Anaconda by running **conda init**. Type "yes" to accept. 
* Install **Spyder** from Anaconda and run it
* Download spike list **rgo_spike_list.csv** from repo
* Download and open the script **Control.py**
* Change location to directory where rgo_spike_list.csv is saved
* Run the script **Control.py**

## Functions
* Receive information (alert signals) from the robot.
* Translate this information into commands compatible with the MaestroPro.
* Efficiently transmit this data to the Maestro system.
* Subsequently, the software will remain in a standby mode, awaiting instructions from the Maestro.
* Upon receiving data from the organoid via the Maestro, your software will analyze it to determine the appropriate next steps.
* The processed information will then be rapidly sent to the robot, and the robot's activity will be monitored.
* Finally, the software will await the next signal from the robot to repeat the cycle.

## Test Dataset
* rgo_spike_list.csv
