This project controls leds in Pimoroni's Plasma Buttons when connected to a Picade controller with Gadgetoid's 
multiverse firmware installed.

See examples.py for a short demo. The demo assumes the buttons have been wired to a Picade Max controller in
the order shown in example_layout.png. It also shows how the coordinate system works. 
The coordinate system should work for any Picade Max, just use utils/ledmap.py and change the button numbers
according to your actual wiring order.