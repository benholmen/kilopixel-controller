# kilopixel controller #
This is the python that reads sensors and controls servos. It runs on a Raspberry Pi directly connected to a grbl board and various sensors.

## Future Improvements ##

- Add a method that iterates over the board and checks pixel values. I expect that some pixels may not be what we think they are so this is error checking.
- Use a REST API instead of connecting directly to the MySQL database. Use this when fetching the next pixel, updating controller status, updating pixel status
- Build the actual kilopixel hardware (!)
