<h1 align="center">
<img src="https://github.com/Grant-Giesbrecht/graf/blob/main/docs/images/graf_banner.png?raw=True" width="800">
</h1><br>

## So what is it?
GrAF is a file format which allows you to save graphs, including the data and format settings. 

## Where does this fit compared to other formats?

There are certainly other formats for saving graphs. One on end of the spectrum, you have 'visual' mechanisms for storing the graph such as PNGs or other bitmap formats. These formats guarantee an accurate representation of your graph, including perfect representation of the styling, however it does not contain the raw data. If you want to access the data later, you'll have to visually infer what the points are.

On the other end of the spectrum, you have the GrAF format. GrAF does not guarantee that the graph will look _exactly_ the same; fonts, line sizes, etc can vary between platforms. However, the core promise of GrAF is that the key aspects of the graph for scientific communication _will_ be retained. The data will be saved as a list of floats in a way that's easy to access, and formatting parameters critical to the visual language of data expression such as graph limits, line types and marker selection, will all be retained. In other words, the data will be accessible, the message of the graph will be preserved, and the formatting can be easily adjusted to match your needs of the day. You can open multiple graf files from previous publications and quickly restyle them to offer a cohesive theme for a new presentation. Or you can quickly merge the data from multiple plots into one, or change the plot type to better convey your point. 

(Mention how SVG sits inbetween bitmaps and GrAF; preserves formatting kinda, is editable, but loses the data.)
(Mention how Pickled figs are great in Python (perfect formatting and data!) but are complex to access due to their formatting sophistication and cannot easily be read in other languages )
(Mention how MATLAB figs are similar to Pklfigs in that they have perfect formatting and store data, but once again, are not easily cross platform and so complex quickly merging files is not trivial. )

(TODO: Add a function to spit out the X and Y data as variables in ipython and/or print to screen.)

The key promise of GrAF is that it will retain the graph data in a way that's easy to access


