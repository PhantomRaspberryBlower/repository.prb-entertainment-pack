# -*- coding: utf-8 -*-

"""
	Venom Add-on
"""

try:
	from sqlite3 import dbapi2 as database
except:
	from pysqlite2 import dbapi2 as database

from resources.lib.modules import control
from resources.lib.modules import log_utils


def clearViews():
	try:
		skin = control.skin
		control.hide()
		if not control.yesnoDialog(control.lang(32056), '', ''): return
		control.makeFile(control.dataPath)
		dbcon = database.connect(control.viewsFile)
		dbcur = dbcon.cursor()
		for t in ['views']:
			try:
				dbcur.execute("DROP TABLE IF EXISTS %s" % t)
				dbcur.execute("VACUUM")
				dbcur.execute("CREATE TABLE IF NOT EXISTS views (""skin TEXT, ""view_type TEXT, ""view_id TEXT, ""UNIQUE(skin, view_type)"");")
				dbcur.connection.commit()
				dbcon.close()
			except:
				log_utils.error()
				pass
		try:
			kodiDB = control.transPath('special://home/userdata/Database')
			kodiViewsDB = control.joinPath(kodiDB, 'ViewModes6.db')
			dbcon = database.connect(kodiViewsDB)
			dbcur = dbcon.cursor()
			dbcur.execute("DELETE FROM view WHERE path LIKE 'plugin://plugin.video.venom/%'")
			dbcur.connection.commit()
			dbcon.close()
		except:
			log_utils.error()
			pass
		skinName = control.addon(skin).getAddonInfo('name')
		skinIcon = control.addon(skin).getAddonInfo('icon')
		control.notification(title=skinName, message=32087, icon=skinIcon)
	except:
		log_utils.error()
		pass


def addView(content):
	try:
		skin = control.skin
		record = (skin, content, str(control.getCurrentViewId()))
		control.makeFile(control.dataPath)
		dbcon = database.connect(control.viewsFile)
		dbcur = dbcon.cursor()
		dbcur.execute("CREATE TABLE IF NOT EXISTS views (""skin TEXT, ""view_type TEXT, ""view_id TEXT, ""UNIQUE(skin, view_type)"");")
		dbcur.execute("DELETE FROM views WHERE skin = '%s' AND view_type = '%s'" % (record[0], record[1]))
		dbcur.execute("INSERT INTO views Values (?, ?, ?)", record)
		dbcur.connection.commit()
		dbcon.close()
		viewName = control.infoLabel('Container.Viewmode')
		skinName = control.addon(skin).getAddonInfo('name')
		skinIcon = control.addon(skin).getAddonInfo('icon')
		control.notification(title=skinName, message=viewName, icon=skinIcon)
	except:
		log_utils.error()
		return


def setView(content, viewDict=None):
	for i in range(0, 200):
		if control.condVisibility('Container.Content(%s)' % content):
			try:
				skin = control.skin
				record = (skin, content)
				dbcon = database.connect(control.viewsFile)
				dbcur = dbcon.cursor()
				dbcur.execute("SELECT * FROM views WHERE skin = '%s' AND view_type = '%s'" % (record[0], record[1]))
				view = dbcur.fetchone()
				if not view: raise Exception()
				view = view[2]
				return control.execute('Container.SetViewMode(%s)' % str(view))
			except:
				try:
					if skin not in viewDict: return
					return control.execute('Container.SetViewMode(%s)' % str(viewDict[skin]))
				except:
					log_utils.error()
					return
		control.sleep(100)