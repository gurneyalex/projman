DATA=data/
GENERATED=generated/

# GENERIC
html: options.html cost.html date.html list.html
xml: options.xml cost.xml date.xml list.xml 
out: options.out cost.out date.out list.out 
all: xml html

# REF
options.out: 
	projman -x --display-duration --display-rates --display-cost ${DATA}simplest_projman.xml  ${DATA}out_options.xml

cost.out: 
	projman -x -v cost ${DATA}simplest_projman.xml  ${DATA}out_simplest_costs.xml
	projman -x -v cost ${DATA}trivial_projman.xml  ${DATA}out_trivial_costs.xml
	projman -x -v cost ${DATA}full_projman.xml  ${DATA}out_full_costs.xml

date.out: 
	projman -x -v date ${DATA}simplest_projman.xml  ${DATA}out_simplest_dates.xml
	projman -x -v date ${DATA}trivial_projman.xml  ${DATA}out_trivial_dates.xml
	projman -x -v date ${DATA}full_projman.xml  ${DATA}out_full_dates.xml

list.out:
	projman -x -v list ${DATA}simplest_projman.xml  ${DATA}out_simplest_list.xml
	projman -x -v list ${DATA}trivial_projman.xml  ${DATA}out_trivial_list.xml
	projman -x -v list ${DATA}full_projman.xml  ${DATA}out_full_list.xml

schedule:
#	simplest
	cp ${DATA}simplest_projman.xml ${DATA}simplest_scheduled_projman.xml
	projman -s -I ${DATA}simplest_scheduled_projman.xml out_simplest_schedule.xml
	mv out_simplest_schedule.xml ${DATA}
#	trivial
	cp ${DATA}trivial_projman.xml ${DATA}trivial_scheduled_projman.xml
	projman -s -I ${DATA}trivial_scheduled_projman.xml out_trivial_schedule.xml
	mv out_trivial_schedule.xml ${DATA}
#	full
	cp ${DATA}full_projman.xml ${DATA}full_scheduled_projman.xml
	projman -s -I ${DATA}full_scheduled_projman.xml out_full_schedule.xml
	mv out_full_schedule.xml ${DATA}

# TEST
options.xml: unittest_writer_docbook.py
	python unittest_writer_docbook.py

date.xml: unittest_writer_dates.py
	python unittest_writer_dates.py

cost.xml: unittest_writer_costs.py
	python unittest_writer_costs.py

list.xml: unittest_writer_list.py
	python unittest_writer_list.py

#HTML
options.html: out_options.html

cost.html: out_simplest_costs.html out_trivial_costs.html out_full_costs.html

date.html: out_simplest_dates.html out_trivial_dates.html out_full_dates.html

list.html: out_simplest_list.html out_trivial_list.html out_full_list.html

out_options.html: ${DATA}out_options.xml
	mkdoc --target=html --stylesheet=single-file ${DATA}out_options.xml
	mv out_options.html ${GENERATED}

out_simplest_costs.html: ${DATA}out_simplest_costs.xml
	mkdoc --target=html --stylesheet=single-file ${DATA}out_simplest_costs.xml
	mv out_simplest_costs.html ${GENERATED}

out_trivial_costs.html: ${DATA}out_trivial_costs.xml
	mkdoc --target=html --stylesheet=single-file ${DATA}out_trivial_costs.xml
	mv out_trivial_costs.html ${GENERATED}

out_full_costs.html: ${DATA}out_full_costs.xml
	mkdoc --target=html --stylesheet=single-file ${DATA}out_full_costs.xml
	mv out_full_costs.html ${GENERATED}

out_simplest_dates.html: ${DATA}out_simplest_dates.xml
	mkdoc --target=html --stylesheet=single-file ${DATA}out_simplest_dates.xml
	mv out_simplest_dates.html ${GENERATED}

out_trivial_dates.html: ${DATA}out_trivial_dates.xml
	mkdoc --target=html --stylesheet=single-file ${DATA}out_trivial_dates.xml
	mv out_trivial_dates.html ${GENERATED}

out_full_dates.html: ${DATA}out_full_dates.xml
	mkdoc --target=html --stylesheet=single-file ${DATA}out_full_dates.xml
	mv out_full_dates.html ${GENERATED}

out_simplest_list.html: ${DATA}out_simplest_list.xml
	mkdoc --target=html --stylesheet=single-file ${DATA}out_simplest_list.xml
	mv out_simplest_list.html ${GENERATED}

out_trivial_list.html: ${DATA}out_trivial_list.xml
	mkdoc --target=html --stylesheet=single-file ${DATA}out_trivial_list.xml
	mv out_trivial_list.html ${GENERATED}

out_full_list.html: ${DATA}out_full_list.xml
	mkdoc --target=html --stylesheet=single-file ${DATA}out_full_list.xml
	mv out_full_list.html ${GENERATED}

