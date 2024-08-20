SRD_CONF_SAMPLERATE = 0
OUTPUT_ANN = 0
OUTPUT_PYTHON = 1
OUTPUT_BINARY = 2
OUTPUT_LOGIC = 3
OUTPUT_META = 4

class Decoder:
	
	cObj = None
	inputs = []
	outputs = []
	tags = []
	channels = ()
	optional_channels = ()
	options = ()
	annotations = ()
	annotation_rows = ()
	binary = ()
	samplenum = 0
	matched = ()

	def has_channel(self, channel):
		return self.cObj.HasChannel(channel)

	def wait(self, conds = None):
		result = self.cObj.Wait(conds)
		if result == None:
			raise Exception("Terminated")
		return result

	def put(self, startsample, endsample, output_id, data):
		self.cObj.Put(startsample, endsample, output_id, data)

	def register (self, output_type, meta = None):
		return self.cObj.Register(output_type, meta)