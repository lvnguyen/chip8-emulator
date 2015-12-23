import os
import sys
import pyglet

KEY_MAP = {pyglet.window.key._1: 0x1,
           pyglet.window.key._2: 0x2,
           pyglet.window.key._3: 0x3,
           pyglet.window.key._4: 0xc,
           pyglet.window.key.Q: 0x4,
           pyglet.window.key.W: 0x5,
           pyglet.window.key.E: 0x6,
           pyglet.window.key.R: 0xd,
           pyglet.window.key.A: 0x7,
           pyglet.window.key.S: 0x8,
           pyglet.window.key.D: 0x9,
           pyglet.window.key.F: 0xe,
           pyglet.window.key.Z: 0xa,
           pyglet.window.key.X: 0,
           pyglet.window.key.C: 0xb,
           pyglet.window.key.V: 0xf
          }

fonts = [0xF0, 0x90, 0x90, 0x90, 0xF0, # 0
       0x20, 0x60, 0x20, 0x20, 0x70, # 1
       0xF0, 0x10, 0xF0, 0x80, 0xF0, # 2
       0xF0, 0x10, 0xF0, 0x10, 0xF0, # 3
       0x90, 0x90, 0xF0, 0x10, 0x10, # 4
       0xF0, 0x80, 0xF0, 0x10, 0xF0, # 5
       0xF0, 0x80, 0xF0, 0x90, 0xF0, # 6
       0xF0, 0x10, 0x20, 0x40, 0x40, # 7
       0xF0, 0x90, 0xF0, 0x90, 0xF0, # 8
       0xF0, 0x90, 0xF0, 0x10, 0xF0, # 9
       0xF0, 0x90, 0xF0, 0x90, 0x90, # A
       0xE0, 0x90, 0xE0, 0x90, 0xE0, # B
       0xF0, 0x80, 0x80, 0x80, 0xF0, # C
       0xE0, 0x90, 0x90, 0x90, 0xE0, # D
       0xF0, 0x80, 0xF0, 0x80, 0xF0, # E
       0xF0, 0x80, 0xF0, 0x80, 0x80  # F
       ]

pixel = pyglet.image.load('pixel.png') # pseudo-pixelwise drawing with 10x10 boxes
buzz = pyglet.resource.media('buzz.wav', streaming=False) 

LOGGING = False

def log(msg):
	if LOGGING:
		print msg

class Chip8(pyglet.window.Window):
	def reset():
		self.graphics = [0] * 64 * 32
		self.delay_timer = 0
		self.sound_timer = 0
		self.stacks = []
		self.registers = [0] * 16
		self.key_state = [0] * 16
		self.index = 0
		self.vx = 0
		self.vy = 0
		self.pc = 0x200
		self.opcode = 0
		self.need_drawing = False
		self.pixel = pixel
		self.buzz = buzz

		# 80 chars
		for i in range(len(fonts)):
			self.memory[i] = fonts[i]

	def __init__(self, *args, **kwargs):
		super(Chip8, self).__init__(args, kwargs)
		self.funcmap = {
			0x0000: self._0ZZZ,
		    0x00e0: self._0ZZ0,
		    0x00ee: self._0ZZE,
		    0x1000: self._1ZZZ,
		    0x2000: self._2ZZZ,
		    0x3000: self._3ZZZ,
		    0x4000: self._4ZZZ,
		    0x5000: self._5ZZZ,
		    0x6000: self._6ZZZ,
		    0x7000: self._7ZZZ,
		    0x8000: self._8ZZZ,
		    0x8FF0: self._8ZZ0,
		    0x8FF1: self._8ZZ1,
		    0x8FF2: self._8ZZ2,
		    0x8FF3: self._8ZZ3,
		    0x8FF4: self._8ZZ4,
		    0x8FF5: self._8ZZ5,
		    0x8FF6: self._8ZZ6,
		    0x8FF7: self._8ZZ7,
		    0x8FFE: self._8ZZE,
		    0x9000: self._9ZZZ,
		    0xA000: self._AZZZ,
		    0xB000: self._BZZZ,
		    0xC000: self._CZZZ,
		    0xD000: self._DZZZ,
		    0xE000: self._EZZZ,
		    0xE00E: self._EZZE,
		    0xE001: self._EZZ1,
		    0xF000: self._FZZZ,
		    0xF007: self._FZ07,
		    0xF00A: self._FZ0A,
		    0xF015: self._FZ15,
		    0xF018: self._FZ18,
		    0xF01E: self._FZ1E,
		    0xF029: self._FZ29,
		    0xF033: self._FZ33,
		    0xF055: self._FZ55,
		    0xF065: self._FZ65
		}

		self.memory = [0] * 4096
		self.reset()
		
	def initialize(rom_file):
		log("Loading %s..." % rom_file)
		self.clear()
		binary = open(rom_file, 'rb')
		# Copy the data from binary to memory
		for i in range(len(binary)):
			self.memory[i + 0x200] = binary[i]
		self.reset()

	def emulateCycle(self):
		self.opcode = (self.memory[self.pc] << 8) | self.memory[self.pc + 1]
		log("Current opcode: %X" % self.opcode)
		self.pc += 2
		self.vx = (self.opcode & 0xf00) >> 8
		self.vy = (self.opcode & 0xf0) >> 4

		extracted_op = (self.opcode & 0xf000)
		try:
			self.funcmap[extracted_op]()
		except:
			print "Unknown instruction %X" % (self.opcode)

		if self.delay_timer > 0:
			self.delay_timer -= 1
		if self.sound_timer > 0:
			self.sound_timer -= 1
			if self.sound_timer == 0:
				self.buzz.play()

	def draw(self):
		if self.need_drawing:
			# Only draw when necessary
			self.clear()
			for i in range(2048):
				if self.graphics[i]:
					self.pixel.blit((i%64)*10, 310 - ((i/64)*10))
			self.flip()
			self.need_drawing = False

	def run():
		while not self.has_exit:
			self.dispatch_events()
			self.emulateCycle()
			self.draw()

if __name__ == "__main__":
	if len(sys.argv) == 1:
		print "Usage: python chip8.py <path to chip8 rom> <log>"
		print "where: <path to chip8 rom> - path to Chip8 rom"
    	print "     : <log> - if present, prints log messages to console"
    else:
    	if len(sys.argv) >= 3:
    		if sys.argv[2] == "log":
    			LOGGING = True

    	width = 640
		height = 320
		chip8 = Chip8(width, height)
		chip8.initialize(sys.argv[1])
		chip8.run()