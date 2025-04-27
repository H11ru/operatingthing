# get the path of this file automatically
mypath = __file__
# split by backslashes
mypath = mypath.split("\\")
# remove the last item
mypath = mypath[:-1]
# append gaime_save.json
mypath.append("gaime_save.json")
# join the path again
mypath = "\\".join(mypath)
# thats the save file we need to remove
if os.path.exists(mypath):
    os.remove(mypath)
# remove virtual file
api.filesystem.delete_file("gaime_save.json")