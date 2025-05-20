# Organoid-Robot-Control
*This is code accompanying the publication*

Molokanova E. _et al._ ** Graphene Optoelectronics for Non-Genetic Neuromodulation in Disease Modeling, Stem Cell Maturation, and Biohybrid Robotics** (2025)

## Installation

* Package: Anaconda, Spyder

## Functions
* Receive information (alert signals) from the robot.
* Translate this information into commands compatible with the MaestroPro.
* Efficiently transmit this data to the Maestro system.
* Subsequently, the software will remain in a standby mode, awaiting instructions from the Maestro.
* Upon receiving data from the organoid via the Maestro, your software will analyze it to determine the appropriate next steps.
* The processed information will then be rapidly sent to the robot, and the robot's activity will be monitored.
* Finally, the software will await the next signal from the robot to repeat the cycle.

## Test Dataset
* rgv_spike_list.csv
