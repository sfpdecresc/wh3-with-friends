# build with [[[pyinstaller --noconsole --onefile wh3.py]]]

import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import TOP
from tkinter import LEFT
from tkinter import BOTTOM
from tkinter.filedialog import askdirectory
from tkinter.filedialog import askopenfilename
from tkinter.filedialog import asksaveasfilename
from tkinter.messagebox import askyesno
from tkinter.messagebox import showinfo
from tkinter.messagebox import showerror
from zipfile import ZipFile
from zipfile import ZIP_DEFLATED
from os.path import realpath
from os.path import relpath
from os.path import normpath
from os.path import commonprefix
import os
import glob
import re
import threading

def getRelativePath(file,dir):
	dir_path = realpath(dir)
	file_path = realpath(file)
	common_prefix = commonprefix([dir_path,file_path])
	if common_prefix != dir_path:
		print("file is not inside the directory")
		exit(1)
	return relpath(file_path,dir_path)

def findDir(name,path):
	for root,dirs,files in os.walk(path):
		if name in dirs and "$RECYCLE.BIN" not in root:
			return os.path.join(root,name)
def findDataFolderHint(_return):
	warhammer = findDir("Total War WARHAMMER III","C:")
	if warhammer is None:
		warhammer = findDir("Total War WARHAMMER III","D:")
	if warhammer is None:
		_return.append(".")
	else:
		_return.append(warhammer + "\\data")

def findMods(dataPath):
	allPacks = glob.glob(dataPath+"\\*.pack")
	modPacks = list(filter(packIsMod,allPacks))
	return modPacks
def packIsMod(pack):
	if re.match(r"^.+?\\audio[^\\]*\.pack$"            ,pack): return False
	if re.match(r"^.+?\\boot\.pack$"                   ,pack): return False
	if re.match(r"^.+?\\campaign_variants[^\\]*\.pack$",pack): return False
	if re.match(r"^.+?\\data[^\\]*\.pack$"             ,pack): return False
	if re.match(r"^.+?\\local[^\\]*\.pack$"            ,pack): return False
	if re.match(r"^.+?\\models[^\\]*\.pack$"           ,pack): return False
	if re.match(r"^.+?\\movies[^\\]*\.pack$"           ,pack): return False
	if re.match(r"^.+?\\shaders[^\\]*\.pack$"          ,pack): return False
	if re.match(r"^.+?\\terrain[^\\]*\.pack$"          ,pack): return False
	if re.match(r"^.+?\\variants[^\\]*\.pack$"         ,pack): return False
	if re.match(r"^.+?\\warmachines[^\\]*\.pack$"      ,pack): return False
	return True

def clean():

	global dataPathHint

	dataPath = askdirectory(
		title="Select WH3's data folder",
		initialdir=dataPathHint)
	if dataPath == "":
		return
	dataPath = normpath(dataPath)
	
	modPacks = findMods(dataPath)
	if len(modPacks) > 0:
		modPacksShort = map(lambda modPack:getRelativePath(modPack,dataPath),modPacks)
		deleteOk = askyesno(
			"Confirmation to delete mods",
			"The following mod files will be deleted. OK?\n"+"\n".join(modPacksShort))
		if deleteOk is False: return
	else:
		showinfo(
			title="Done",
			message="No mods found, so nothing to delete.")
		return

	pbStart()
	for modPack in modPacks:
		os.remove(modPack)
	pbStop()

	showinfo(
		title="Mods deleted",
		message="Mods deleted.")

def unpack():

	global dataPathHint

	part1Path = askopenfilename(
		title="Select WH3's data folder",
		initialdir=dataPathHint,
		filetypes=(("zip file part 1","*.zip.part1"),))
	if part1Path == "":
		return
	part1Path = normpath(part1Path)

	dataPath = askdirectory(
		title="Select WH3's data folder",
		initialdir=dataPathHint)
	if dataPath == "":
		return
	dataPath = normpath(dataPath)
	
	modPacks = findMods(dataPath)
	if len(modPacks) > 0:
		modPacksShort = map(lambda modPack:getRelativePath(modPack,dataPath),modPacks)
		deleteOk = askyesno(
			"Confirmation to delete mods",
			"The following mod files will be deleted. OK?\n"+"\n".join(modPacksShort))
		if deleteOk is False: return
	
	pbStart()
	update("removing old mods...")
	for modPack in modPacks:
		os.remove(modPack)
	update("combining parts...")
	zipPath = combine(part1Path)
	update("extracting mods...")
	with ZipFile(zipPath,"r") as zip:
		zip.extractall(dataPath)
	os.remove(zipPath)
	pbStop()

	showinfo(
		title="Mods mirrored",
		message="Mods mirrored successfully.")

def pack():
	
	global dataPathHint

	dataPath = askdirectory(
		title="Select WH3's data folder",
		initialdir=dataPathHint)
	if dataPath == "":
		return
	dataPath = normpath(dataPath)

	modPacks = findMods(dataPath)
	if len(modPacks) == 0:
		showerror(
			title="No mods found",
			message="No mods found in WH3's data folder.")
		return
	
	destination = asksaveasfilename(
		title="Select a basename for the destination zip file",
		defaultextension=".zip",
		initialdir=dataPathHint,
		initialfile="wh3mods.zip")
	if destination == "":
		return
	destination = normpath(destination)
	
	pbStart()
	oldParts = glob.glob(destination+".part*")
	for oldPart in oldParts:
		os.remove(oldPart)
	update("compressing and packing mods...")
	with ZipFile(destination,"w",ZIP_DEFLATED,True,1) as zip:
		for modPack in modPacks:
			rel = getRelativePath(modPack,dataPath)
			update("packing "+rel)
			zip.write(modPack,rel)
	update("splitting archive...")
	parts = split(destination,500*1024*1024)
	pbStop()

	showinfo(
		title="Success",
		message="Share the following files with your friends:\n"+"\n".join(parts))

def update(text):
	global label
	label.configure(text=text)
	root.update_idletasks()
	root.update()
def pbStart():
	update("working...")
def pbStop():
	update("")

def split(filename,chunksize):
	ret = []
	with open(filename,"rb") as f:
		i = 1
		while True:
			bytes = f.read(chunksize)
			if len(bytes) == 0 or bytes is None:
				break
			else:
				partname = filename+".part"+str(i)
				ret.append(partname)
				with open(partname,"wb") as f2:
					f2.write(bytes)
				i += 1
	os.remove(filename)
	return ret

def combine(part1):
	base = part1.removesuffix(".part1")
	if base == part1:
		exit(1)
	with open(base,"wb") as fdest:
		i = 1
		while True:
			try:
				with open(base+".part"+str(i),"rb") as f:
					fdest.write(f.read())
			except IOError:
				break
			i += 1
	return base

root = tk.Tk()
root.title("Mirror WH3 Mods w/Friends (ver1)")
root.resizable(False, False)

label = ttk.Label(root)
label.grid(row=0,column=0,columnspan=3,padx=(12,12),pady=(12,0))
ttk.Button(root,text="Remove all data folder mods",command=clean).grid(row=1,column=0,padx=(12,0),pady=(12,12))
ttk.Button(root,text="Unpack a friend's mods",command=unpack).grid(row=1,column=1,padx=(12,0),pady=(12,12))
ttk.Button(root,text="Pack your mods for a friend",command=pack).grid(row=1,column=2,padx=(12,12),pady=(12,12))

first = True
doneFinding = False
_return = []
stop = False
#root.mainloop()
def on_closing():
	global stop
	stop = True
root.protocol("WM_DELETE_WINDOW",on_closing)
while True:
	if stop:
		root.destroy()
		break
	root.update_idletasks()
	root.update()
	if first:
		pbStart()
		thr = threading.Thread(target=findDataFolderHint, args=(_return,), kwargs={})
		thr.start() # Will run "foo"
		first = False
	if not doneFinding and not thr.is_alive():
		doneFinding = True
		thr.join()
		dataPathHint = _return[0]
		pbStop()