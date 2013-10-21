# Copyright 2007 Andrey Falko
#
# Program is distributed under the terms 
# of the GNU General Public License
DB_DIR=/var/db/maint/
USER=apache
GROUP=apache

install:
	mkdir -p ${DESTDIR}/usr/bin
	cp maint ${DESTDIR}/usr/bin/maint
	cp maint-daemon ${DESTDIR}/usr/bin/maint-daemon
	mkdir -p ${DESTDIR}/var/run/maint
	chown apache:apache ${DESTDIR}/var/run/maint
	chmod 770 ${DESTDIR}/var/run/maint
	mkdir -p ${DESTDIR}/var/log/maint
	chown apache:apache ${DESTDIR}/var/log/maint
	chmod 770 ${DESTDIR}/var/log/maint
	mkdir -p ${DESTDIR}/etc
	cp maint.conf.example ${DESTDIR}/etc/maint.conf.example

sqlite:
	mkdir -p ${DESTDIR}$(DB_DIR)
	chown $(USER):$(GROUP) ${DESTDIR}$(DB_DIR)
	chmod 770 ${DESTDIR}$(DB_DIR)
	sqlite3 ${DESTDIR}$(DB_DIR)maint.db < db/blankdb.sqlite
	chown $(USER):$(GROUP) ${DESTDIR}$(DB_DIR)maint.db

clean:
	rm ${DESTDIR}$(DB_DIR)maint.db
