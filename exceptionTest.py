from inspect import currentframe as cf
from inspect import getframeinfo as gf
excRep = []
try:
	finfo = gf(cf())
	print (crap)
except Exception as err:
	exc = (finfo.filename,str(finfo.lineno),str(type(err))[8:-2],str(err))
	excRep.append(exc)
	print(exc)
try:
	finfo = gf(cf())
	print (crap)
except Exception as err:
	exc = (finfo.filename,str(finfo.lineno),str(type(err))[8:-2],str(err))
	excRep.append(exc)
	print(exc)
	print("\n",excRep)
