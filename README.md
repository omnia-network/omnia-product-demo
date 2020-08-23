Omnia Remote OS

  ### Requirements
 1. python packages:
     ```
     pip3 install -r requirements.txt
     ```

  2. Arial font (take a look also [here](https://askubuntu.com/a/651442/)):

      ```
     sudo apt-get install ttf-mscorefonts-installer
     sudo fc-cache
     fc-match Arial
     ```
  
  2. On the **ESP32**, you must install the `uasyncio` library (take a look also [here](https://github.com/peterhinch/micropython-async/blob/master/TUTORIAL.md#hardware-with-internet-connectivity)):

      ```
      import upip
      upip.install('micropython-uasyncio')
      upip.install('micropython-uasyncio.synchro')
      upip.install('micropython-uasyncio.queues')
     ```
