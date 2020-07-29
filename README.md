Air quality degradation is an alarming issue in metropolitan cities like Delhi NCR. Degraded air quality leads to adverse effects on human health leading to issues like respiratory diseases and even environmental dis-balance like acid rain and global warming, further degrading human health. Also, the data is changing according to weather changes and other factors, which our traditional algorithms may not handle properly. We propose a method for implementing an algorithm that works with real-time data of air quality prediction. We have a continuous stream of data coming from various sources and that data is changing on a day-to-day basis, but our traditional algorithms take all of the data at once and then prepare a model for the same Thus, if the data changes we have to discard the previous model and re-implement the model with new examples. This leads to more time and space complexity. Hoeffding Tree is a classifier which works on streaming data, by creating a Hoeffding bound through which we ensure the number of instances to be run in order to achieve a certain level of confidence.
