#if defined(WIN32) || defined(WIN64) || defined (linux)
#include <Python.h>
#else 
#include <Python/Python.h>
#endif
 
#include <iostream>
#include <DataManager.h>
#include <DataParser.h>
#include <Correlator.h>
#include <AutoCorrelator.h>

#include <FilterManager.h>
#include <CullFilter.h>
#include <DecimateFilter.h>
#include <GaussianFilter.h>

DataManager manager;
Correlator correlator;
AutoCorrelator autocorrelator;
FilterManager filter_manager;

std::string g_data("");
bool logfilter = false;

Data* dataptr = NULL;
Data* logdataptr = NULL;

using namespace std;

// local utility functions
static bool getTypeAndAnnot(char *typeStr, int &outType, char **outAnnot);
static int getType(char *typeStr);


// prototypes
static PyObject* initialize(PyObject *self, PyObject *args);
static PyObject* openHoleFile(PyObject *self, PyObject *args);
static PyObject* getData(PyObject *self, PyObject *args);
static PyObject* getHoleData(PyObject *self, PyObject *args);
static PyObject* getDataAtDepth(PyObject *self, PyObject *args);
static PyObject* getRange(PyObject *self, PyObject *args);
static PyObject* getRatio(PyObject *self, PyObject *args);
static PyObject* finalize(PyObject *self, PyObject *args);
static PyObject* composite(PyObject *self, PyObject *args);
static PyObject* project(PyObject *self, PyObject *args);
static PyObject* projectAll(PyObject *self, PyObject *args);
static PyObject* evalcoef(PyObject *self, PyObject *args);
static PyObject* evalcoef_splice(PyObject *self, PyObject *args);
static PyObject* evalcoefLog(PyObject *self, PyObject *args);
static PyObject* splice(PyObject *self, PyObject *args);
static PyObject* init_splice(PyObject *self, PyObject *args);
static PyObject* sagan(PyObject *self, PyObject *args);
static PyObject* delete_sagan(PyObject *self, PyObject *args);
static PyObject* fixed_sagan(PyObject *self, PyObject *args);
static PyObject* setSagan(PyObject *self, PyObject *args);
static PyObject* setSaganOption(PyObject *self, PyObject *args);
static PyObject* delete_splice(PyObject *self, PyObject *args);
static PyObject* first_splice(PyObject *self, PyObject *args);
static PyObject* squish(PyObject *self, PyObject *args);
static PyObject* openStratFile(PyObject *self, PyObject *args);
static PyObject* openAttributeFile(PyObject *self, PyObject *args);
static PyObject* openLogFile(PyObject *self, PyObject *args);
static PyObject* writeLogFile(PyObject *self, PyObject *args);
static PyObject* openSpliceFile(PyObject *self, PyObject *args);
static PyObject* loadAltSpliceFile(PyObject *self, PyObject *args);
static PyObject* initAltSplice(PyObject *self, PyObject *args);
static PyObject* saveAttributeFile(PyObject *self, PyObject *args);
static PyObject* saveSpliceFile(PyObject *self, PyObject *args);
static PyObject* cleanData(PyObject *self, PyObject *args);
static PyObject* cleanDataType(PyObject *self, PyObject *args);
static PyObject* decimate(PyObject *self, PyObject *args);
static PyObject* smooth(PyObject *self, PyObject *args);
static PyObject* cull(PyObject *self, PyObject *args);
static PyObject* setLogFilter(PyObject *self, PyObject *args);
static PyObject* bestCoreMatch(PyObject *self, PyObject *args);
static PyObject* correlate(PyObject *self, PyObject *args);
static PyObject* initCorrelate(PyObject *self, PyObject *args);
static PyObject* setCorrelate(PyObject *self, PyObject *args);
static PyObject* prevCorrelate(PyObject *self, PyObject *args);
static PyObject* applyCorrelate(PyObject *self, PyObject *args);
static PyObject* undoCorrelate(PyObject *self, PyObject *args);
static PyObject* openCullTable(PyObject *self, PyObject *args);
static PyObject* saveCullTable(PyObject *self, PyObject *args);
static PyObject* saveCoreData(PyObject *self, PyObject *args);
static PyObject* saveAgeCoreData(PyObject *self, PyObject *args);
static PyObject* undo(PyObject *self, PyObject *args);
static PyObject* setEnable(PyObject *self, PyObject *args);
static PyObject* setEvalGraph(PyObject *self, PyObject *args);
static PyObject* getAveDepStep(PyObject *self, PyObject *args);
static PyObject* getMudline(PyObject *self, PyObject *args);
static PyObject* append(PyObject *self, PyObject *args);
static PyObject* append_at_begin(PyObject *self, PyObject *args);
static PyObject* append_selected(PyObject *self, PyObject *args);
static PyObject* undoAppend(PyObject *self, PyObject *args);
static PyObject* setAgeOrder(PyObject *self, PyObject *args);
static PyObject* createNewAge(PyObject *self, PyObject *args);
static PyObject* formatChange(PyObject *self, PyObject *args);
static PyObject* setCoreQuality(PyObject *self, PyObject *args);
static PyObject* getMcdRate(PyObject *self, PyObject *args);
static PyObject* getSectionAtDepth(PyObject *self, PyObject *args);
static PyObject* setDelimiter(PyObject *self, PyObject *args);

#if defined(WIN32) || defined(CORRELATOR_MACOSX)
PyMODINIT_FUNC initpy_correlator(void);
#elif defined(WIN64)
PyMODINIT_FUNC initpy_correlator64(void);
#else
#error "WIN32 or WIN64 must be defined"
#endif

// all the methods callable from Python have to be
// listed here
static PyMethodDef PyCoreMethods[] = {
    {"initialize", initialize, METH_VARARGS,
     "Initialize Correlator data manager."},

    {"finalize", finalize, METH_VARARGS,
     "Finalize Correlator data manager."},

    {"openHoleFile", openHoleFile, METH_VARARGS,
     "Open Hole data file."},

    {"getData", getData, METH_VARARGS,
     "Get Core Data."},

    {"getHoleData", getHoleData, METH_VARARGS,
     "Get Hole Core Data."},

    {"getDataAtDepth", getDataAtDepth, METH_VARARGS,
     "Get Core Data At Depth."},

    {"getRange", getRange, METH_VARARGS,
     "Get Range."},

    {"getRatio", getRatio, METH_VARARGS,
     "Get Ratio."},

    {"composite", composite, METH_VARARGS,
     "Composite Data."},

    {"project", project, METH_VARARGS,
     "Composite Shift one core by given offset."},

     {"projectAll", projectAll, METH_VARARGS,
      "Composite Shift all cores in a hole by given rate."},

    {"evalcoef", evalcoef, METH_VARARGS,
     "Evaluate Cores."},

    {"evalcoef_splice", evalcoef_splice, METH_VARARGS,
     "Evaluate Splice Cores."},

    {"evalcoefLog", evalcoefLog, METH_VARARGS,
     "Evaluate Log and Core."},

    {"splice", splice, METH_VARARGS,
     "Splice Data."},

    {"init_splice", init_splice, METH_VARARGS,
     "Initialize Splice Data."},

    {"sagan", sagan, METH_VARARGS,
     "Sagan Data."},

    {"delete_sagan", delete_sagan, METH_VARARGS,
     "Delete Sagan Data."},

    {"fixed_sagan", fixed_sagan, METH_VARARGS,
     "Fixed Sagan Data."},

    {"setSagan", setSagan, METH_VARARGS,
     "Set Sagan Option."},

    {"setSaganOption", setSaganOption, METH_VARARGS,
     "Set Sagan Option."},

    {"first_splice", first_splice, METH_VARARGS,
     "First Splice Data."},

    {"delete_splice", delete_splice, METH_VARARGS,
     "Delete Splice Data."},

    {"squish", squish, METH_VARARGS,
     "Squish Data."},

    {"openStratFile", openStratFile, METH_VARARGS,
     "Open Strat data file."},

    {"openAttributeFile", openAttributeFile, METH_VARARGS,
     "Open Affine data file."},
	 
    {"openLogFile", openLogFile, METH_VARARGS,
     "Open Log data file."},

    {"writeLogFile", writeLogFile, METH_VARARGS,
     "Write Log data file."},

    {"openSpliceFile", openSpliceFile, METH_VARARGS,
     "Open Splice data file."},

    {"initAltSplice", initAltSplice, METH_VARARGS,
     "Init Alternative Splice data."},

    {"loadAltSpliceFile", loadAltSpliceFile, METH_VARARGS,
     "Load Alternative Splice data file."},

    {"saveAttributeFile", saveAttributeFile, METH_VARARGS,
     "Save Affine data file."},

    {"saveSpliceFile", saveSpliceFile, METH_VARARGS,
     "Save Splice data file."},

    {"cleanData", cleanData, METH_VARARGS,
     "Clean data."},

    {"cleanDataType", cleanDataType, METH_VARARGS,
     "Clean data Type."},

    {"decimate", decimate, METH_VARARGS,
     "Decimate data."},

    {"smooth", smooth, METH_VARARGS,
     "Smooth data."},

    {"cull", cull, METH_VARARGS,
     "Cull data."},

    {"setLogFilter", setLogFilter, METH_VARARGS,
     "Set Log Filter."},

    {"bestCoreMatch", bestCoreMatch, METH_VARARGS,
     "Get Best Correlate Match."},

    {"correlate", correlate, METH_VARARGS,
     "Correlate data."},

    {"initCorrelate", initCorrelate, METH_VARARGS,
     "Initialize Correlate data."},

    {"setCorrelate", setCorrelate, METH_VARARGS,
     "Set Correlate data."},

    {"prevCorrelate", prevCorrelate, METH_VARARGS,
     "Preview Best Correlate."},

    {"applyCorrelate", applyCorrelate, METH_VARARGS,
     "Apply Best Correlate."},

    {"undoCorrelate", undoCorrelate, METH_VARARGS,
     "Undo Best Correlate."},

    {"openCullTable", openCullTable, METH_VARARGS,
     "Open cull table"},

    {"saveCullTable", saveCullTable, METH_VARARGS,
     "Save cull table"},

    {"saveCoreData", saveCoreData, METH_VARARGS,
     "Save Core Data"},

    {"saveAgeCoreData", saveAgeCoreData, METH_VARARGS,
     "Save Age Core Data"},

    {"undo", undo, METH_VARARGS,
     "Undo data."},

    {"setEnable", setEnable, METH_VARARGS,
     "Set enable."},

    {"setEvalGraph", setEvalGraph, METH_VARARGS,
     "Set Eval Graph Config."},

    {"getAveDepStep", getAveDepStep, METH_VARARGS,
     "Get Average Depth Step."},

    {"getMudline", getMudline, METH_VARARGS,
     "Get Mudline."},

    {"getMcdRate", getMcdRate, METH_VARARGS,
     "Get Mcd/mbsf Rate."},

    {"append", append, METH_VARARGS,
     "Append Splice."},

    {"append_at_begin", append_at_begin, METH_VARARGS,
     "Append Core after the first spliced core."},

    {"append_selected", append_selected, METH_VARARGS,
     "Append Selected Core"},

    {"undoAppend", undoAppend, METH_VARARGS,
     "Undo Append Splice."},

    {"setAgeOrder", setAgeOrder, METH_VARARGS,
     "Set Age Order."},

    {"createNewAge", createNewAge, METH_VARARGS,
     "Create New Age."},

    {"formatChange", formatChange, METH_VARARGS,
     "Change format."},

    {"setCoreQuality", setCoreQuality, METH_VARARGS,
     "Set Core Quality."},

    {"getSectionAtDepth", getSectionAtDepth, METH_VARARGS,
     "Given a hole and core, get section number at provided depth." },

     {"setDelimiter", setDelimiter, METH_VARARGS,
      "Set delimiter used for writing files: 0 = space + tab, 1 = comma." },

    {NULL, NULL, 0, NULL}        /* Sentinel */
};


// this function is called when we do import py_correlator from python
// it let's the python interpreter know about all the functions
// in this module available for calling
#if defined(WIN32) || defined(CORRELATOR_MACOSX)
PyMODINIT_FUNC initpy_correlator(void)
#elif defined(WIN64)
PyMODINIT_FUNC initpy_correlator64(void)
#else
#error "WIN32 or WIN64 must be defined"
#endif
{
#if defined(WIN32) || defined(CORRELATOR_MACOSX)
	(void) Py_InitModule("py_correlator", PyCoreMethods);
#elif defined(WIN64)
	(void) Py_InitModule("py_correlator64", PyCoreMethods);
#endif
	
	autocorrelator.setCorrelator(&correlator);

}

// initializes the core object from python
static PyObject* initialize(PyObject *self, PyObject *args)
{
	char *pathDir;

	// parse the arguments
	if (!PyArg_ParseTuple(args, "s", &pathDir))
		return NULL;

        manager.registerPath(pathDir);
        //manager.printPaths();

	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject* finalize(PyObject *self, PyObject *args)
{
	if(dataptr)
	{
		delete dataptr;
		dataptr = NULL;
	}
	//std::cout << "Closed py_correlator" << std::endl;

	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject* openHoleFile(PyObject *self, PyObject *args)
{
	//int holeID;
	char *fileName;
	int format;
	int deciValue;
	int cull;
	float culltop, cullstrength;
	int cullno;
	float value1, value2;
 	int sign1, sign2, join;
	int smooth, smooth_unit;
	int display;
	int coretype;
	char *annotation;

	// parse the arguments
	if (!PyArg_ParseTuple(args, "siiiififffiiiiiis", &fileName, &format, &coretype,  &deciValue, &cull, &culltop, &cullno, &cullstrength, &value1, &value2, &sign1, &sign2, &join, &smooth, &smooth_unit, &display, &annotation))
		return NULL;

	if(coretype == 1) 
		coretype = GRA;
	else if(coretype == 2) 
		coretype = PWAVE;
	else if(coretype == 3)	
		coretype = SUSCEPTIBILITY;
	else if(coretype == 4)	
		coretype = NATURALGAMMA;
	else if(coretype == 5)	
		coretype = REFLECTANCE;
	else if(coretype == 6)	
		coretype = OTHERTYPE;
	else if(coretype == 7)
		coretype = USERDEFINEDTYPE;

	manager.setCoreType(coretype);

	if(format == -1)	
		manager.setCoreFormat(INTERNAL_REPORT);
	else if(format == 1)	
		manager.setCoreFormat(MST95REPORT);
	else if(format == 2)	
		manager.setCoreFormat(TKREPORT);
	else if(format == 3)	
		manager.setCoreFormat(ODPOTHER);
	else if(format == 4)	
		manager.setCoreFormat(JANUSORIG);

	Data* tempptr = NULL;
	string stranno = annotation;
	if (stranno.size() == 0)
		tempptr = manager.load(fileName, dataptr);
	else {
		tempptr = manager.load(fileName, dataptr, annotation);
	}

	if(tempptr)
	{
	    dataptr = tempptr;
		filter_manager.setData(dataptr);
		dataptr->update();
		dataptr->update();

		correlator.assignData(dataptr);

		if (cull == 1)
		{
			CullFilter* cullfilter = NULL;
			cullfilter = filter_manager.getCullFilter(tempptr->getLeg(), tempptr->getSite(), coretype, annotation);
			cullfilter->setEnable(true);
			cullfilter->setCullTop(culltop);
			if(cullno != -1)
			{
				cullfilter->setCullCoreNo(cullno);
			}
			cullfilter->setCullSignal(cullstrength);
			cullfilter->setEquation(value1, value2, sign1, sign2, join);
			//std::cout << "value1 " << value1 << " : " << value2 << " sign : " << sign1 << " : " << sign2 << " : " << join << std::endl;
		} 

		if(deciValue >= 1) 
		{
			DecimateFilter* decifilter = NULL;
			decifilter = filter_manager.getDeciFilter(tempptr->getLeg(), tempptr->getSite(), coretype, annotation);
			decifilter->setEnable(true);
			decifilter->setNumber(deciValue);
		}
		if (smooth > 0)
		{
			GaussianFilter* smoothfilter = NULL;
			smoothfilter = filter_manager.getSmoothFilter(tempptr->getLeg(), tempptr->getSite(), coretype, annotation);
			smoothfilter->setEnable(true);
			if(smooth_unit == 1)
			{
				smoothfilter->setUnit(POINTS);
				smoothfilter->setWidth(smooth);
			} else if(smooth_unit == 2)
			{
				smoothfilter->setUnit(DEPTH);
				data_range* range = dataptr->getRange();
				//std::cout << "range : " << range->maxdepthdiff << std::endl;
				smoothfilter->setDepth(smooth, range->maxdepth);
			}
		}
		filter_manager.apply();

		//dataptr->debugPrintOut();
		return Py_BuildValue("i", 1);
	}
	
	return Py_BuildValue("i", 0);
}


static PyObject* setLogFilter(PyObject *self, PyObject *args)
{
	int deciValue;
	int cull;
	float culltop, cullstrength;
	int cullno;
	float value1, value2;
 	int sign1, sign2, join;

	// parse the arguments
	if (!PyArg_ParseTuple(args, "iififffiii", &deciValue, &cull, &culltop, &cullno, &cullstrength, &value1, &value2, &sign1, &sign2, &join))
		return NULL;

	/* 
	HYEJUNG NOW
	logfilter = true;
	decifilter.setNumber(1);
	if(deciValue >= 1) 
	{
		decifilter.setEnable(true);
		decifilter.setNumber(deciValue);
	}

	logcullfilter.setEnable(false);
	if (cull == 1)
	{
		logcullfilter.setEnable(true);
		logcullfilter.setCullTop(culltop);
		if(cullno != -1)
		{
			logcullfilter.setCullCoreNo(cullno);
		}
		logcullfilter.setCullSignal(cullstrength);
		logcullfilter.setEquation(value1, value2, sign1, sign2, join);
		//std::cout << "log value1 " << value1 << " : " << value2 << " sign : " << sign1 << " : " << sign2 << " : " << join << std::endl;
		logcullfilter.setMethod(CULL_PARAMETERS);

	}
	*/

	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject* decimate(PyObject *self, PyObject *args)
{
	int deciValue;
	char* type;

	if (!PyArg_ParseTuple(args, "si", &type, &deciValue))
		return NULL;

	if(dataptr && (deciValue >= 1))
	{
		int coretype = USERDEFINEDTYPE;
		char* annotation = NULL;
		getTypeAndAnnot(type, coretype, &annotation);

		DecimateFilter* decifilter = NULL;
		filter_manager.setData(dataptr);
		decifilter = filter_manager.getDeciFilter(dataptr->getLeg(), dataptr->getSite(), coretype, annotation);

		decifilter->setEnable(true);
		decifilter->setNumber(deciValue);
		filter_manager.apply();
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject* smooth(PyObject *self, PyObject *args)
{
	int smooth, smooth_unit;
	char* type;

	if (!PyArg_ParseTuple(args, "sii", &type, &smooth, &smooth_unit))
		return NULL;

	if (smooth > 0)
	{
		int coretype = USERDEFINEDTYPE;
		char* annotation = NULL;
		getTypeAndAnnot(type, coretype, &annotation);

		if (coretype == SPLICE)
		{
			filter_manager.setSpliceHole(correlator.getSpliceHole());
			filter_manager.setSaganHole(correlator.getHolePtr(ELD_RECORD));
		}

		GaussianFilter* smoothfilter = NULL;
		filter_manager.setData(dataptr);
		smoothfilter = filter_manager.getSmoothFilter(dataptr->getLeg(), dataptr->getSite(), coretype, annotation);
		if (smoothfilter == NULL)
		{
			//cout << "could not get pointer" << endl;
			Py_INCREF(Py_None);
			return NULL;
		}

		if(smooth_unit == -1)
		{
			smoothfilter->setEnable(false);
		}

		if(smooth_unit == 1)
		{
			smoothfilter->setEnable(true);
			smoothfilter->setUnit(POINTS);
			smoothfilter->setWidth(smooth);
			//std::cout << "width : " << smooth << std::endl;
		} else if(smooth_unit == 2)
		{
			//cout << "smooth unit : depth " << endl;
			smoothfilter->setEnable(true);
			smoothfilter->setUnit(DEPTH);
			data_range* range = dataptr->getRange();
			//std::cout << "range : " << range->maxdepthdiff << " " << range->maxdepth << std::endl;
			smoothfilter->setDepth(smooth, range->maxdepth);
		}
		filter_manager.apply();
	}
	Py_INCREF(Py_None);
	return Py_None;
}


static PyObject* getAveDepStep(PyObject *self, PyObject *args)
{
	float avedepthstep = 0.0f;
	data_range* range = NULL;
	if(dataptr)
	{
		range = dataptr->getRange();
		if (range)
			avedepthstep = (float) (range->avedepstep);
	}

	return Py_BuildValue("f", avedepthstep);
}

static PyObject* getMcdRate(PyObject *self, PyObject *args)
{
	float depth;

	if (!PyArg_ParseTuple(args, "f", &depth))
		return NULL;

	float rate = (float)(correlator.getRate(depth));

	return Py_BuildValue("f", rate);
}

static PyObject* getMudline(PyObject *self, PyObject *args)
{
	float mudline = 0.0; 
	if(dataptr)
	{
		mudline = (float)(dataptr->getMudLine());
	}

	return Py_BuildValue("f", mudline);
}

static PyObject* bestCoreMatch(PyObject *self, PyObject *args)
{
	AutoCorrResult* result=NULL;
	result = autocorrelator.getBestCorrelate();

	return Py_BuildValue("fffff", result->m_squish, result->m_offset,result->m_coef,result->m_rate,result->m_b);
}

static PyObject* correlate(PyObject *self, PyObject *args)
{
	float squish, offset;
        if (!PyArg_ParseTuple(args, "ff", &squish, &offset))
                return NULL;

	double rate, b;
	int ret = autocorrelator.correlate(squish, offset, rate, b);

	if (ret == 1) 
	{
        	return Py_BuildValue("ff", (float)rate, (float)b);
	}

	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject* initCorrelate(PyObject *self, PyObject *args)
{
	autocorrelator.undoToAll();
	autocorrelator.init();

	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject* setCorrelate(PyObject *self, PyObject *args)
{
	char* hole_name;
	char* type;
	float squish_start, squish_end, squish_interval;
	float offset_start, offset_end, offset_interval;
	float depth_step;
	
	if (!PyArg_ParseTuple(args, "ssfffffff", &hole_name, &type, &squish_start, &squish_end, &squish_interval, &offset_start, &offset_end, &offset_interval,&depth_step))
		return NULL;

	dataptr->update();
	logdataptr = correlator.getLogData();
	if(logdataptr)
	{
		logdataptr->update();
	}

	if(strcmp(hole_name, "Splice") == 0)
	{
		Hole* coreptr = correlator.getSpliceHole();
		autocorrelator.addHole(coreptr);
	} else 
	{
		int coretype = USERDEFINEDTYPE;
		char* annotation = NULL;
		getTypeAndAnnot(type, coretype, &annotation);

		autocorrelator.addHole(hole_name, coretype, annotation);
	}

	autocorrelator.setSquishRange(squish_start, squish_end, squish_interval);
	autocorrelator.setOffsetRange(offset_start, offset_end, offset_interval);
	autocorrelator.setDepthStep(depth_step);
	autocorrelator.setCorrelate();

	//autocorrelator.correlate();
	//autocorrelator.applyBest();
	//dataptr->update();
	//dataptr->update();

	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject* prevCorrelate(PyObject *self, PyObject *args)
{
	int flag;
	float squish;
	float offset;

        if (!PyArg_ParseTuple(args, "iff", &flag, &squish, &offset))
                return NULL;

	if (flag == 0)
		autocorrelator.applyBest();
	else
		autocorrelator.apply(squish, offset);

	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject* applyCorrelate(PyObject *self, PyObject *args)
{
	int flag;
	float squish;
	float offset;

        if (!PyArg_ParseTuple(args, "iff", &flag, &squish, &offset))
                return NULL;

	if (flag == 0) 
		autocorrelator.applyBestToAll();
	else 
		autocorrelator.applyToAll(squish, offset);
	dataptr->update();
	dataptr->update();

	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject* undoCorrelate(PyObject *self, PyObject *args)
{
	int all_flag;
	
        if (!PyArg_ParseTuple(args, "i", &all_flag))
                return NULL;

	if(all_flag == 0)
	{
		autocorrelator.undo();
	} else 
	{
		autocorrelator.undoToAll();
	}
	dataptr->update();
	dataptr->update();

	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject* cull(PyObject *self, PyObject *args)
{
	int cull;
	float culltop, cullstrength;
	int cullno;
	float value1, value2;
	int sign1, sign2, join;
	char* type;

	if (!PyArg_ParseTuple(args, "sififffiii", &type, &cull, &culltop, &cullno, &cullstrength, &value1, &value2, &sign1, &sign2, &join))
		return NULL;

	int coretype = USERDEFINEDTYPE;
	char* annotation = NULL;
	getTypeAndAnnot(type, coretype, &annotation);

	filter_manager.setData(dataptr);
	if (cull == 1)
	{
		CullFilter* cullfilter = NULL;
		cullfilter = filter_manager.getCullFilter(dataptr->getLeg(), dataptr->getSite(), coretype, annotation);
		if(cullfilter->getMethod() == CULL_TABLE)
		{
			dataptr->reset(CULL_TABLE, coretype, annotation);
			dataptr->update();
		}

		cullfilter->setEnable(true);
		cullfilter->setCullTop(culltop);
		cullfilter->setCullCoreNo(cullno);
		cullfilter->setCullSignal(cullstrength);
		cullfilter->setEquation(value1, value2, sign1, sign2, join);

		//std::cout << "[DEBUG] value1 " << value1 << " : " << value2 << " sign : " << sign1 << " : " << sign2 << " : " << join << std::endl;
		cullfilter->setMethod(CULL_PARAMETERS);
		filter_manager.apply();
	} else 
	{
		CullFilter* cullfilter = NULL;
		cullfilter = filter_manager.getCullFilter(dataptr->getLeg(), dataptr->getSite(), coretype, annotation);
		cullfilter->setEnable(false);
		filter_manager.apply();
	}


	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject* openCullTable(PyObject *self, PyObject *args)
{
	char *fileName = NULL;
	int coretype;
	char* annotation = NULL;
	if (!PyArg_ParseTuple(args, "sis", &fileName, &coretype, &annotation))
		return NULL;

	if(coretype == 1)
		coretype = GRA;
	else if(coretype == 2)
		coretype = PWAVE;
	else if(coretype == 3)
		coretype = SUSCEPTIBILITY;
	else if(coretype == 4)
		coretype = NATURALGAMMA;
	else if(coretype == 5)
		coretype = REFLECTANCE;
	else if(coretype == 6)
		coretype = OTHERTYPE;
	else if(coretype == 7)
		coretype = USERDEFINEDTYPE;

	if(fileName)
	{
		CullFilter* cullfilter = NULL;
		filter_manager.setData(dataptr);
		cullfilter = filter_manager.getCullFilter(dataptr->getLeg(), dataptr->getSite(), coretype, annotation);
		int ret = cullfilter->create(fileName);
		if (ret == 1)
		{
			manager.loadCullTable(fileName, coretype, dataptr, annotation);
		} 
		if (ret >= 0)
		{
			manager.setCullFile(fileName);
			cullfilter->setEnable(true);
			//cout << "open cull " << coretype << " " << annotation << endl;
			filter_manager.apply();
		}
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject* saveCullTable(PyObject *self, PyObject *args)
{
	char *fileName = NULL;
	char *type = NULL;
	if (!PyArg_ParseTuple(args, "ss", &fileName, &type))
		return NULL;

	if(fileName)
	{
		int coretype = USERDEFINEDTYPE;
		char* annotation = NULL;
		getTypeAndAnnot(type, coretype, &annotation);

		CullFilter* cullfilter = NULL;
		filter_manager.setData(dataptr);
		cullfilter = filter_manager.getCullFilter(dataptr->getLeg(), dataptr->getSite(), coretype, annotation);

		cullfilter->openCullTable(fileName, type);
		filter_manager.apply();
		cullfilter->closeCullTable();
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject* saveCoreData(PyObject *self, PyObject *args)
{
	char *fileName = NULL;
	int type;

	if (!PyArg_ParseTuple(args, "si", &fileName, &type))
		return NULL;

	int ret = 0;
	if(fileName != NULL)
	{
		if (type == 0)
		{
			dataptr->update();
			dataptr->update();
			ret = manager.save(fileName, dataptr);
		}
		else if (type == 1)
		{
			ret = manager.saveHole(fileName, correlator.getHolePtr(SPLICED_RECORD));
		} else if (type == 2)
		{
			correlator.generateSaganHole();
			ret = manager.saveHole(fileName, correlator.getHolePtr(ELD_RECORD));
		}
	}

	//Py_INCREF(Py_None);
	return Py_BuildValue("i", ret);
}

static PyObject* saveAgeCoreData(PyObject *self, PyObject *args)
{
	char *fileName = NULL;
	char *ageFileName = NULL;
	int type;

	if (!PyArg_ParseTuple(args, "ssi", &ageFileName, &fileName, &type))
		return NULL;
	//cout << ageFileName << " " << fileName << " " << type << endl;

	int ret = 0;
	if(fileName != NULL)
	{
		if (type == 0)
		{
			dataptr->update();
			dataptr->update();
			ret = manager.saveTimeSeries(ageFileName, fileName, dataptr);
		}
		else if (type == 1)
		{
			ret = manager.saveTimeSeriesHole(ageFileName, fileName, correlator.getHolePtr(SPLICED_RECORD));
		} else if (type == 2)
		{
			correlator.generateSaganHole();
			ret = manager.saveTimeSeriesHole(ageFileName, fileName, correlator.getHolePtr(ELD_RECORD));
		}
	}

	//Py_INCREF(Py_None);
	return Py_BuildValue("i", ret);
}

static PyObject* setEnable(PyObject *self, PyObject *args)
{
        int deci, cull, smooth;

        if (!PyArg_ParseTuple(args, "iii", &deci, &smooth, &cull))
                return NULL;

	/* 
	HYEJUNG NOW
	if(dataptr)
	{
		dataptr->init(QUALITY);
		if (deci == 1) // decimate
		{
			dataptr->accept(&decifilter);
			dataptr->update();
		} else if (cull ==1) // cull
		{
			dataptr->accept(&cullfilter);
			dataptr->update();
		} else if (smooth == 1) // smooth 
		{
			dataptr->accept(&smoothfilter);
			dataptr->update();
		}
	}
	*/

	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject* setEvalGraph(PyObject *self, PyObject *args)
{
	float depthstep, winlen, leadlag;

	if (!PyArg_ParseTuple(args, "fff", &depthstep, &winlen, &leadlag))
		return NULL;

	correlator.setDepthStep(depthstep);
	correlator.setWinLen(winlen);
	correlator.setLeadLagMeters(leadlag);

	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject* undo(PyObject *self, PyObject *args)
{
	int flag;
	char* hole;
	int coreid;

	if (!PyArg_ParseTuple(args, "isi", &flag, &hole, &coreid))
		return NULL;

	if(dataptr)
	{
		if (flag == 1)
			correlator.undo();
		else if (flag == 2)
			correlator.undoAbove(hole, coreid);
	}

	Py_INCREF(Py_None);
	return Py_None;
}


static PyObject* getRatio(PyObject *self, PyObject *args)
{
	char* holename;
	char* type;

	if (!PyArg_ParseTuple(args, "ss", &holename, &type))
		return NULL;

	int coretype = USERDEFINEDTYPE;
	char* annotation = NULL;
	getTypeAndAnnot(type, coretype, &annotation);

	float ratio =0.0f;
	if (coretype == LOGTYPE) 
	{
		logdataptr = manager.getLogData();
		if (logdataptr != NULL)
		{
			ratio = (float)(logdataptr->getRatio());
			return Py_BuildValue("f", ratio);
		}
	} else if (coretype == SPLICE) 
	{
		Hole* holeptr = correlator.getHolePtr(SPLICED_RECORD);
		if (holeptr != NULL)
		{
			ratio = holeptr->getRatio();
			return Py_BuildValue("f", ratio);
		}

	} else 
	{
		if (dataptr != NULL)
		{
			Hole* holeptr = dataptr->getHole(holename, coretype, annotation);
			if (holeptr == NULL) 
				ratio = 1.0;
			else 
				ratio = holeptr->getRatio();
		}
	}
	return Py_BuildValue("f", ratio);
}


static PyObject* getRange(PyObject *self, PyObject *args)
{
	char* type;
	if (!PyArg_ParseTuple(args, "s", &type))
		return NULL;

	int coretype = USERDEFINEDTYPE;
	char* annotation = NULL;
	getTypeAndAnnot(type, coretype, &annotation);

	double min, max;
	if (coretype == LOGTYPE) 
	{
		logdataptr = manager.getLogData();
		if (logdataptr != NULL)
		{
			//logdataptr->getTypeRange(coretype, annotation, min, max);
			min = (float)(logdataptr->getMin());
			max = (float)(logdataptr->getMax());
			return Py_BuildValue("ff", (float)min, (float)max);
		}
	} else 
	{
		if (dataptr != NULL)
		{
			dataptr->getTypeRange(coretype, annotation, min, max);
			return Py_BuildValue("ff", (float)min, (float)max);
		}
	}

	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject* getDataAtDepth(PyObject *self, PyObject *args)
{
	// HEEEEEEEEEE
	char* hole;
	int coreid; 
	float pos;
	char* type;

	if (!PyArg_ParseTuple(args, "sifs", &hole, &coreid, &pos, &type))
	{
		return NULL;
	}

	char* annotation = NULL;
	int coretype = USERDEFINEDTYPE;
	getTypeAndAnnot(type, coretype, &annotation);

	float ret = (float)(correlator.getDataAtDepth(hole, coreid, pos, coretype, annotation));
	return Py_BuildValue("f", ret);
}

static PyObject* getData(PyObject *self, PyObject *args)
{
	int smoothed_data;

	if (!PyArg_ParseTuple(args, "i", &smoothed_data))
		return NULL;

	g_data = ""; 
	if(dataptr) 
	{
		switch (smoothed_data)
		{
		case 0 :	// Data 
			dataptr->getTuple(g_data, DATA);
			break;
		case 1 : 	// Smooth data
			dataptr->getTuple(g_data, SMOOTH);
			break;
		case 2 : 	// splice tie info 
			correlator.getSpliceTuple(g_data);
			break;
		case 3 :	// splice hole data 
			correlator.generateSpliceHole();
			correlator.getTuple(g_data, SPLICEDATA);
			break;
		case 4 :	// splice hole smooth data 
			correlator.generateSpliceHole();
			correlator.getTuple(g_data, SPLICESMOOTH);
			break;
		case 7 :	// strat data 
			if(dataptr != NULL)
			{
				dataptr->getTuple(g_data, STRAT_TABLE);
			}
			break;
		case 8 :	// log splice hole data 
			//cout << "case 8 " << endl;
			correlator.generateSaganHole();
			correlator.getTuple(g_data, LOG);
			break;
		case 9 :	// log splice hole data 
			correlator.getTuple(g_data, DATA);
			break;
		case 10 :	// log splice hole data 
			correlator.generateSaganHole();
			correlator.getTuple(g_data, LOGSMOOTH);
			break;
		case 11 :	// log splice hole data 
			correlator.getTuple(g_data, SMOOTH);
			break;
		case 12 :	// sagan tie info
			correlator.getSaganTuple(g_data);
			break;
		case 13 :	// sagan tie info
			correlator.getSaganTuple(g_data, true);
			break;
		case 14 :	// log splice hole data 
			//cout << "case 14 " << endl;
			correlator.getTuple(g_data, LOG);
			break;
		case 15 :	// splice hole data 
			correlator.getTuple(g_data, SPLICEDATA);
			break;
		case 16 :	// splice hole smooth data 
			correlator.getTuple(g_data, SPLICESMOOTH);
			break;
		case 17 :	// log splice hole data 
			correlator.getTuple(g_data, LOGSMOOTH);
			break;
		case 18 :	// section data
			if(dataptr != NULL)
			{
				dataptr->getTuple(g_data, SECTION);
			}
			break;
		case 20 :	// sagan tie data
			if(dataptr != NULL)
			{
				dataptr->getTuple(g_data, SAGAN_TIE);
			}
			break;
		case 21 :	// composite tie data
			if(dataptr != NULL)
			{
				dataptr->getTuple(g_data, TIE_SHIFT);
			}
			break;
		}
	}
	
	if(logdataptr)
	{
		if (smoothed_data == 5)
		{
			logdataptr->getTuple(g_data, DATA);
			// for testing : dataptr = logdataptr;
		}	
		else if (smoothed_data == 19)
		{
			logdataptr->getTuple(g_data, SMOOTH);
		}
	}

	//std::cout << data << std::endl;

	return Py_BuildValue("s", g_data.c_str());
}

static PyObject* getHoleData(PyObject *self, PyObject *args)
{
	int hole_num;
	int smooth;

	if (!PyArg_ParseTuple(args, "ii", &hole_num, &smooth))
		return NULL;

	g_data = ""; 
	if(dataptr) 
	{
		if (smooth == 2)
        	correlator.getTuple(g_data, hole_num, SPLICESMOOTH);
		else 
        	correlator.getTuple(g_data, hole_num, SPLICEDATA);
	}

	return Py_BuildValue("s", g_data.c_str());
}


static PyObject* composite(PyObject *self, PyObject *args)
{
	char* holeA;
	char* holeB;
	int coreidA, coreidB; 
	float posA, posB;
	int opt;
	char* type;
	char* comment;

	if (!PyArg_ParseTuple(args, "sifsifiss", &holeA, &coreidA, &posA, &holeB, &coreidB, &posB, &opt, &type, &comment))
	{
		return NULL;
	}

	char* annotation = NULL;
	int coretype = USERDEFINEDTYPE;
	getTypeAndAnnot(type, coretype, &annotation);

	float ret = 0.0;
	if (opt == 2) // shift this core to tie/evaluation
		ret = (float) (correlator.composite(holeA, coreidA, posA, holeB, coreidB, posB, coretype, annotation, comment));
	else if(opt == 3) // shift this core and all below to tie/evaluation
		ret = (float) (correlator.compositeBelow(holeA, coreidA, posA, holeB, coreidB, posB, coretype, annotation, comment));
	else if (opt == 4) // shift this core to given
		ret = (float) (correlator.composite(holeA, coreidA, posB, coretype, annotation, comment));
	else if (opt == 5) // shift this core and all below to given
		ret = (float) (correlator.compositeBelow(holeA, coreidA, posB, coretype, annotation, comment));
	else
		cout << "Unknown composite operation " << opt << ", expected 2-5" << endl;

	//correlator.generateSpliceHole();

	//Py_INCREF(Py_None);
	//return Py_None;
	return Py_BuildValue("f", ret);
}

static PyObject* project(PyObject *self, PyObject *args)
{
	char *hole = NULL;
	int core = 0;
	char *datatypeStr = NULL;
	float offset = 0.0f;
	char *comment = NULL;

	if (!PyArg_ParseTuple(args, "sisfs", &hole, &core, &datatypeStr, &offset, &comment))
		return NULL;

	char* annotation = NULL;
	int datatype = USERDEFINEDTYPE;
	getTypeAndAnnot(datatypeStr, datatype, &annotation);

	float ret = (float) correlator.project(hole, core, datatype, annotation, offset, comment);

	return Py_BuildValue("f", ret);
}

static PyObject* projectAll(PyObject *self, PyObject *args)
{
	char *hole = NULL;
	char *datatypeStr = NULL;
	float rate = 0.0f;
	char *comment = NULL;

	if (!PyArg_ParseTuple(args, "ssfs", &hole, &datatypeStr, &rate, &comment))
		return NULL;

	char* annotation = NULL;
	int datatype = USERDEFINEDTYPE;
	getTypeAndAnnot(datatypeStr, datatype, &annotation);

	float ret = (float) correlator.projectAll(hole, datatype, annotation, rate, comment);

	return Py_BuildValue("f", ret);
}


static PyObject* evalcoef(PyObject *self, PyObject *args)
{
	char* holeA;
	char* holeB;
	char* typeA;
	char* typeB;
	int coreidA, coreidB; 
	float posA, posB;

	if (!PyArg_ParseTuple(args, "ssifssif", &typeA, &holeA, &coreidA, &posA, &typeB, &holeB, &coreidB, &posB))
		return NULL;

	//cout << holeA[0] << " " << coreidA << " " << posA << " " << holeB[0] << " " << coreidB << " " << posB << endl;

	int coretypeA = USERDEFINEDTYPE;
	char* annotationA = NULL;
	getTypeAndAnnot(typeA, coretypeA, &annotationA);

	int coretypeB = USERDEFINEDTYPE;
	char* annotationB = NULL;
	getTypeAndAnnot(typeB, coretypeB, &annotationB);

	int ret=0;
	ret = correlator.evalCore(coretypeA, annotationA, holeA, coreidA, posA, coretypeB, annotationB, holeB, coreidB, posB);

	g_data = "";
	if(ret > 0) 
	{
		correlator.getCoefList(g_data);
	}

	return Py_BuildValue("s", g_data.c_str());
}

static PyObject* evalcoef_splice(PyObject *self, PyObject *args)
{
	char* holeA;
	char* typeA;
	int coreidA;
	float posA, posB;

	if (!PyArg_ParseTuple(args, "ssiff", &typeA, &holeA, &coreidA, &posA, &posB))
		return NULL;

	int coretypeA = USERDEFINEDTYPE;
	char* annotationA = NULL;
	getTypeAndAnnot(typeA, coretypeA, &annotationA);

	int ret=0;
	ret = correlator.evalSpliceCore(coretypeA, annotationA, holeA, coreidA, posA, posB);

	g_data = "";
	if(ret > 0) 
	{
		correlator.getCoefList(g_data);
	}

	return Py_BuildValue("s", g_data.c_str());
}
static PyObject* evalcoefLog(PyObject *self, PyObject *args)
{
	char* holeA;
	int coreidA;
	float posA, posB;

	if (!PyArg_ParseTuple(args, "siff", &holeA, &coreidA, &posA, &posB))
		return NULL;

	int ret=0;
	ret = correlator.evalCoreLog(holeA, coreidA, posA, posB);

	g_data = "";
	if(ret > 0) 
	{
		correlator.getCoefList(g_data);
	}

	return Py_BuildValue("s", g_data.c_str());
}


static PyObject* first_splice(PyObject *self, PyObject *args)
{
	char* hole;
	int coreid;
	int smooth;
	int append;
	char* type;

	if (!PyArg_ParseTuple(args, "siiis", &hole, &coreid, &smooth, &append, &type))
		return NULL;

	//cout << " type = " << type << endl;
	int coretype = USERDEFINEDTYPE;
	char* annotation = NULL;
	getTypeAndAnnot(type, coretype, &annotation);

	int ret;
	if (append == 0)
		ret = correlator.splice(hole, coreid, coretype, annotation);
	else
		ret = correlator.splice(hole, coreid, coretype, annotation, true); // brg never called

	g_data = ""; 
	if(ret > 0 ) 
	{
		if (smooth == 2)
        		correlator.getTuple(g_data, SPLICESMOOTH);
		else 
        		correlator.getTuple(g_data, SPLICEDATA);
	}

        return Py_BuildValue("s", g_data.c_str());
}

static PyObject* setAgeOrder(PyObject *self, PyObject *args)
{
	int idx;
	float depth;
	char* name;
	if (!PyArg_ParseTuple(args, "ifs", &idx, &depth, &name))
		return NULL;

	correlator.setAgeSeries(idx, depth, name);
	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject* createNewAge(PyObject *self, PyObject *args)
{
	float depth;
	float age;
	char* name;
	if (!PyArg_ParseTuple(args, "ffs", &depth, &age, &name))
		return NULL;

	Py_INCREF(Py_None);
	return Py_None;
}


static PyObject* formatChange(PyObject *self, PyObject *args)
{
	char* infile;
	char* outfile;
	if (!PyArg_ParseTuple(args, "ss", &infile, &outfile))
		return NULL;

	manager.changeFormat(infile, outfile);
	
	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject* setCoreQuality(PyObject *self, PyObject *args)
{
	char* hole;
	int coreid;
	int quality;
	char* type;

	if (!PyArg_ParseTuple(args, "siis", &hole, &coreid, &quality, &type))
		return NULL;

	int coretype = USERDEFINEDTYPE;
	char* annotation = NULL;
	getTypeAndAnnot(type, coretype, &annotation);
	correlator.setCoreQuality(hole, coreid, coretype, quality, annotation);

	//cout << " type ==> " << type << " " << coretype << endl;

	CullFilter* cullfilter = NULL;
	cullfilter = filter_manager.getCullFilter(dataptr->getLeg(), dataptr->getSite(), coretype, annotation);

	cullfilter->setEnable(true);
	
	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject* undoAppend(PyObject *self, PyObject *args)
{
	int smooth;
	if (!PyArg_ParseTuple(args, "i", &smooth))
		return NULL;

	int ret = correlator.undoAppendSplice();

	correlator.generateSpliceHole();
	g_data = "";
	if(ret > 0 ) 
	{
		if (smooth == 2)
       		correlator.getTuple(g_data, SPLICESMOOTH);
		else
			correlator.getTuple(g_data, SPLICEDATA);
	}

	return Py_BuildValue("is", ret, g_data.c_str());
}

static PyObject* append_at_begin(PyObject *self, PyObject *args)
{
	correlator.splice();
	correlator.generateSpliceHole();
	return Py_None;
}

static PyObject* append(PyObject *self, PyObject *args)
{
	int type;
	int smooth;
	if (!PyArg_ParseTuple(args, "ii", &type, &smooth))
		return NULL;

	int ret = 1;
	if (type == 1)
	{
		ret = correlator.appendSplice(true);
	} else 
	{
		ret = correlator.appendSplice(false);
	}

	correlator.generateSpliceHole();

	g_data = "";
	if(ret > 0 ) 
	{
		if (smooth == 2)
       		correlator.getTuple(g_data, SPLICESMOOTH);
		else
			correlator.getTuple(g_data, SPLICEDATA);
	}

	return Py_BuildValue("is", ret, g_data.c_str());
}

static PyObject* append_selected(PyObject *self, PyObject *args)
{
	char* type;
	char* hole;
	int coreid; 
	int smooth;
	if (!PyArg_ParseTuple(args, "ssii", &type, &hole, &coreid, &smooth))
		return NULL;

	int coretype = USERDEFINEDTYPE;
	char* annot = NULL;
	getTypeAndAnnot(type, coretype, &annot);

	int ret = correlator.appendSelectedSplice(coretype, annot, hole, coreid);
	correlator.generateSpliceHole();

	g_data = "";
	if(ret > 0 ) 
	{
		if (smooth == 2)
       		correlator.getTuple(g_data, SPLICESMOOTH);
		else
			correlator.getTuple(g_data, SPLICEDATA);
	}

	return Py_BuildValue("is", ret, g_data.c_str());
}

static PyObject* splice(PyObject *self, PyObject *args)
{
	char* holeA;
	char* holeB;
	int coreidA, coreidB; 
	float posA, posB;
	int tieNo;
	int smooth;
	int append;
	bool appendflag = false;
	char* typeA;
	char* typeB;

	if (!PyArg_ParseTuple(args, "ssifssifiii", &typeA, &holeA, &coreidA, &posA, &typeB, &holeB, &coreidB, &posB, &tieNo, &smooth, &append))
		return NULL;

	if (append == 1)
		appendflag = true;
	
	//cout << "[DEBUG] type A = " << typeA << " type B = " << typeB << " " << posA << " " << posB << endl;
	int coretypeA = USERDEFINEDTYPE;
	char* annotA = NULL;
	getTypeAndAnnot(typeA, coretypeA, &annotA);

	int coretypeB = USERDEFINEDTYPE;
	char* annotB = NULL;
	getTypeAndAnnot(typeB, coretypeB, &annotB);

	int ret  = correlator.splice(tieNo, coretypeA, annotA, holeA, coreidA, posA, coretypeB, annotB, holeB, coreidB, posB, appendflag);
	dataptr->update();
	dataptr->update();

	correlator.generateSpliceHole();

	float depth = -999.0;
	g_data = "";
	if(ret > 0 ) 
	{
		Value* tiePnt = correlator.getTiePoint();
		if (tiePnt != NULL)
			depth = (float)(tiePnt->getELD()); 

		if (smooth == 2)
        		correlator.getTuple(g_data, SMOOTH);
		else
        		correlator.getTuple(g_data);
	}

	return Py_BuildValue("isf", ret, g_data.c_str(), depth);
}


static PyObject* sagan(PyObject *self, PyObject *args)
{
	char* holeA;
	char* holeB;
	int coreidA, coreidB; 
	float posA, posB;
	int tieNo;

	if (!PyArg_ParseTuple(args, "sifsifi", &holeA, &coreidA, &posA, &holeB, &coreidB, &posB, &tieNo))
		return NULL;

	//int ret  = correlator.sagan(tieNo, holeA[0], coreidA, posA, holeB[0], coreidB, posB);
	int ret  = correlator.sagan(tieNo, holeA, coreidA, posA, holeB, coreidB, posB);
	char* name = (char*) correlator.getSaganCoreName();
	dataptr->update();
	dataptr->update();

	float depth = -999.0;
	Value* tiePnt = correlator.getTiePoint();
	if (tiePnt != NULL)
		depth = (float)(tiePnt->getELD()); 

	correlator.generateSagan();
	correlator.generateSaganHole();

    return Py_BuildValue("isf", ret, name, depth);
}

static PyObject* delete_sagan(PyObject *self, PyObject *args)
{
	int tieid; 

	if (!PyArg_ParseTuple(args, "i", &tieid))
		return NULL;

	int ret = 1;
	g_data = "";
	if(tieid == -1)
	{
		// DELETE ALL	
		//correlator.deleteAllSplice();
		//dataptr->update();
	} else 
	{
		ret  = correlator.deleteSagan(tieid);
		//dataptr->update();
		//dataptr->update();

		correlator.generateSagan();
		//correlator.updateTies();
		//correlator.generateSagan();
		correlator.generateSaganHole();
	}
        return Py_BuildValue("i", ret);
}

static PyObject* fixed_sagan(PyObject *self, PyObject *args)
{
	//correlator.sagan();

	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject* setSagan(PyObject *self, PyObject *args)
{
	int flag;
	if (!PyArg_ParseTuple(args, "i", &flag))
		return NULL;

	bool coreflag = true;
	if(flag == 1)
	{
		coreflag = false;
	}

	correlator.setCoreOnly(coreflag);

	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject* setSaganOption(PyObject *self, PyObject *args)
{
	int flag;
	if (!PyArg_ParseTuple(args, "i", &flag))
		return NULL;

	bool floating_flag = false;
	if(flag == 1)
	{
		floating_flag = true;
	}

	correlator.setFloating(floating_flag);

	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject* delete_splice(PyObject *self, PyObject *args)
{
	int tieid; 
	int smooth;

	if (!PyArg_ParseTuple(args, "ii", &tieid, &smooth))
		return NULL;

	int ret;
	g_data = "";
	if(tieid == -1)
	{
		// DELETE ALL	
		correlator.deleteAllSplice();
		dataptr->update();
	} else 
	{
		ret  = correlator.deleteSplice(tieid);
		dataptr->update();
		dataptr->update();

		correlator.generateSpliceHole();
		if(ret == 1 ) 
		{
			if (smooth == 2)
        			correlator.getTuple(g_data, SMOOTH);
			else 
        			correlator.getTuple(g_data);
		}
	}

	return Py_BuildValue("s", g_data.c_str());
}


static PyObject* init_splice(PyObject *self, PyObject *args)
{
	correlator.initSplice();
	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject* squish(PyObject *self, PyObject *args)
{
	char* hole;
	int coreid;
	float squish;

	if (!PyArg_ParseTuple(args, "sif", &hole, &coreid, &squish))
		return NULL;

	//EXAMPPLE squish(2, 95)

	correlator.squish(hole, coreid, squish);
        if(dataptr)
        {
                dataptr->update();
                dataptr->update();
	}

	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject* openStratFile(PyObject *self, PyObject *args)
{
	char* fileName;
	char* stratType;
	int type;

	if (!PyArg_ParseTuple(args, "ss", &fileName, &stratType))
		return NULL;

	type = 0;
	if (strcmp(stratType, "Radioloria") == 0)
		type = 1;
	else if (strcmp(stratType, "Foraminifera") == 0)
		type = 2;
	else if (strcmp(stratType, "Nannofossils") == 0)
		type = 3;
	else if (strcmp(stratType, "Paleomag") == 0)
		type = 4;

	manager.setStratType(type);
	Data* tempptr = NULL;
	tempptr = manager.load(fileName, dataptr);
	autocorrelator.applyToAll();

	if(tempptr)
	{
		dataptr = tempptr;
		dataptr->update();
		dataptr->update();
		return Py_BuildValue("i", 1);
	}

	return Py_BuildValue("i", 0);
}

static PyObject* openAttributeFile(PyObject *self, PyObject *args)
{
	char* fileName;
	int mode;

	if (!PyArg_ParseTuple(args, "si", &fileName, & mode))
		return NULL;

	Data* tempdataptr = manager.load(fileName, dataptr);
	autocorrelator.applyToAll();
	int ret = 0;

	if(tempdataptr)
	{
		ret = 1;
		dataptr = tempdataptr;
		correlator.generateSpliceHole();
		dataptr->update();
		dataptr->update();
	}
	if (mode == 1)
	{
		correlator.makeUpELD(); 
		//correlator.generateSagan();
		correlator.generateSaganHole();
	}

    return Py_BuildValue("i", ret);
	//Py_INCREF(Py_None);
	//return Py_None;
}


static PyObject* openLogFile(PyObject *self, PyObject *args)
{
	char* fileName;
	int selectedColumn;

	if (!PyArg_ParseTuple(args, "si", &fileName, &selectedColumn))
		return NULL;

	// selectedColumn == 0 : get header
 	// selectedColumn > 0 : load log 
	manager.setSelectedColumn(selectedColumn);
	manager.load(fileName, dataptr);

	string* loginfo = NULL;
	if(selectedColumn == 0) 
	{
		loginfo = manager.getLogInfo();
	} else 
	{
		logdataptr = manager.getLogData();
	
		if(logdataptr)
		{
			if (logdataptr->getNumOfHoles() == 0)
   				return Py_BuildValue("s", "");

			correlator.setLogData(logdataptr);
			filter_manager.setLogData(logdataptr);
			if(logfilter == true)
			{
				/* 
				HYEJUNG NOW
				logdataptr->init(QUALITY);
				logdataptr->accept(&decifilter);
				logdataptr->accept(&cullfilter);
				*/
			}
			autocorrelator.applyToAll();
			logdataptr->update();
			logdataptr->update();
   			return Py_BuildValue("s", "1");
		}
	}

	if(loginfo != NULL)
	{
        	return Py_BuildValue("s", loginfo->c_str());
	}

   	return Py_BuildValue("s", "");

	//Py_INCREF(Py_None);
	//return Py_None;
}

static PyObject* writeLogFile(PyObject *self, PyObject *args)
{
	char* read;
	char* write;
	int depth_idx;
	int data_idx;

	if (!PyArg_ParseTuple(args, "ssii", &read, &write, &depth_idx, &data_idx))
		return NULL;

	manager.save(read, write, depth_idx, data_idx);
	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject* openSpliceFile(PyObject *self, PyObject *args)
{
	char* fileName;

	if (!PyArg_ParseTuple(args, "s", &fileName))
		return NULL;

	Data* tempdataptr = manager.load(fileName, dataptr);

	g_data = ""; 
	if(tempdataptr)
	{
		dataptr = tempdataptr;
		dataptr->update();
		dataptr->update();
		correlator.generateSpliceHole();
		//correlator.getTuple(g_data);
	} else 
	{
		g_data = "error"; 
	}

	return Py_BuildValue("s", g_data.c_str());
}

static PyObject* initAltSplice(PyObject *self, PyObject *args)
{
   	correlator.initiateAltSplice();
	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject* loadAltSpliceFile(PyObject *self, PyObject *args)
{
        char* fileName;
		char* type;

        if (!PyArg_ParseTuple(args, "ss", &fileName, &type))
                return NULL;

		int coretype = USERDEFINEDTYPE;
		char* annotation = NULL;
		getTypeAndAnnot(type, coretype, &annotation);

		g_data = ""; 
		if (dataptr != NULL)
		{
			Data* tempdataptr = manager.loadAltSplice(fileName, dataptr, coretype, annotation);
        	if(tempdataptr)
			{
                dataptr->update();
                dataptr->update();
        		correlator.generateAltSpliceHole(g_data);
			}
		}

        return Py_BuildValue("s", g_data.c_str());

}

static PyObject* saveSpliceFile(PyObject *self, PyObject *args)
{
	char* fileName;
	char* affinename;

	if (!PyArg_ParseTuple(args, "ss", &fileName, &affinename))
		return NULL;
	manager.save( fileName, dataptr, affinename );
	Py_INCREF(Py_None);
	return Py_None;

}

static PyObject* saveAttributeFile(PyObject *self, PyObject *args)
{
	char* fileName;
	int type;

	if (!PyArg_ParseTuple(args, "si", &fileName, &type))
		return NULL;

	if(type == 1)
	{	
		manager.save( fileName, dataptr, AFFINE_TABLE );
	}
	else if(type == 2)
	{
		manager.save( fileName, dataptr, SPLICE_TABLE );
	}	
	else if(type == 3) // brg 9/10/2014 unused
	{
		manager.save( fileName, correlator.getSpliceHole(), dataptr->getLeg(), dataptr->getSite() );
	}
	else if(type == 4)
	{
		manager.save( fileName, dataptr, EQLOGDEPTH_TABLE );
	}
	else if(type == 5) // brg 9/10/2014 unused
	{
		if (logdataptr)
			manager.save( fileName, logdataptr, LOG );
	}
	else if(type == 6) // brg 9/10/2014 unused
	{
		manager.save( fileName, dataptr, SPLICER_AGE );
	}
	else if(type == 7) // brg 9/10/2014 unused
	{
		manager.save( fileName, correlator.getSpliceHole(), dataptr->getLeg(), dataptr->getSite(), true );
	}

	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject* cleanDataType(PyObject *self, PyObject *args)
{
	char* type;

	if (!PyArg_ParseTuple(args, "s", &type))
		return NULL;

	int datatype = GRA;
	std::string strtype = type;

	if(strtype.find("Bulk Density(GRA)") != string::npos)
		datatype = GRA;
	else if(strtype.find("Pwave") != string::npos)
		datatype = PWAVE;
	else if(strtype.find("PWave") != string::npos)
		datatype = PWAVE;
	else if(strtype.find("Susceptibility") != string::npos)
		datatype = SUSCEPTIBILITY;
	else if(strtype.find("Natural Gamma") != string::npos)
		datatype = NATURALGAMMA;
	else if(strtype.find("NaturalGamma") != string::npos)
		datatype = NATURALGAMMA;
	else if(strtype.find("Reflectance") != string::npos)
		datatype = REFLECTANCE;
	else if(strtype.find("Other Type") != string::npos)
		datatype = OTHERTYPE;
	else if(strtype.find("ODP Other1") != string::npos)
		datatype = ODPOTHER1;
	else if(strtype.find("ODP Other2") != string::npos)
		datatype = ODPOTHER2;
	else if(strtype.find("ODP Other3") != string::npos)
		datatype = ODPOTHER3;
	else if(strtype.find("ODP Other4") != string::npos)
		datatype = ODPOTHER4;
	else if(strtype.find("ODP Other5") != string::npos)
		datatype = ODPOTHER5;

	//std::cout << "type " << strtype << " " << datatype << std::endl;
	manager.cleanCore(dataptr, datatype);

	Py_INCREF(Py_None);
	return Py_None;
}


static PyObject* cleanData(PyObject *self, PyObject *args)
{
	int type;

	if (!PyArg_ParseTuple(args, "i", &type))
		return NULL;

	//std::cout << "clean data --- " << type << std::endl;

	if(dataptr)
	{	
		if(type == 1)
     	{
			correlator.initSplice();
			correlator.init();
			manager.init();
			logfilter = false;
			logdataptr = manager.getLogData();
			correlator.setLogData(logdataptr);
			autocorrelator.init();
           	delete dataptr;
           	dataptr = NULL;

			filter_manager.init();
      	}
		else if(type == 2)
		{
           	dataptr->init(ALL_TIE);
			correlator.init();
			correlator.clearLogData(0);
			dataptr->update();
			dataptr->update();
       	}
		else if(type == 3)
		{
           	dataptr->init(COMPOSITED_TIE);
			correlator.init(COMPOSITED_TIE);
			dataptr->update();
			dataptr->update();
       	}
		else if(type == 4)
		{
           	dataptr->init(REAL_TIE);
			correlator.init(REAL_TIE);
			dataptr->update();
			dataptr->update();
		}
		else if(type == 5)
		{	
			correlator.clearLogData();
			manager.cleanLog();
			logdataptr = manager.getLogData();
			correlator.setLogData(logdataptr);
			logfilter = false;
           	dataptr->update();
            dataptr->update();
		}
		else if(type == 6)
		{	
			correlator.clearStratData();
			manager.cleanStrat();
       	}
		else if(type == 7)
		{
           	dataptr->init(REAL_TIE, true);
			correlator.init(REAL_TIE);
			manager.cleanSplice();
			dataptr->update();
			dataptr->update();
		}
		else if(type == 8)
		{
			//std::cout << "--------------------------- " << std::endl;
           		dataptr->init(STRETCH);
			correlator.init();
			correlator.clearLogData();
			autocorrelator.init();
			dataptr->update();
			dataptr->update();
		}
		else if(type == 9)
		{
			correlator.clearLogData(0);
			dataptr->update();
			dataptr->update();
			correlator.generateSagan();
			correlator.generateSaganHole();
		}
	}

	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject* getSectionAtDepth(PyObject *self, PyObject *args)
{
	char *holeName = NULL;
	char *typeName = NULL;
	int coreIndex = -1;
	float depth = 0.0f;

	if (!PyArg_ParseTuple(args, "sisf", &holeName, &coreIndex, &typeName, &depth))
		return NULL;

	const int coreType = getType(typeName);
	const int sectionNumber = correlator.getSectionAtDepth(holeName, coreIndex, coreType, (double)depth);

	return Py_BuildValue("i", sectionNumber);
}

static PyObject* setDelimiter(PyObject *self, PyObject *args)
{
	int delimiter = -1;
	if (!PyArg_ParseTuple(args, "i", &delimiter))
		return NULL;

	SetDelimiter(delimiter);

	Py_INCREF(Py_None);
	return Py_None;
}

static int getType(char *typeStr)
{
	int coreType = -1;

	if (strcmp(typeStr, "All Holes") == 0)
		coreType = ALL;
	else if ((strcmp(typeStr, "All Bulk Density(GRA)") == 0) || (strcmp(typeStr, "Bulk Density(GRA)") == 0))
		coreType = GRA; 
	else if ((strcmp(typeStr, "All Pwave") == 0) || (strcmp(typeStr, "Pwave") == 0) || (strcmp(typeStr, "All PWave") == 0) || (strcmp(typeStr, "PWave") == 0))
		coreType = PWAVE;
	else if ((strcmp(typeStr, "All Susceptibility") == 0) || (strcmp(typeStr, "Susceptibility") == 0))
		coreType = SUSCEPTIBILITY; 
	else if ((strcmp(typeStr, "All Natural Gamma") == 0) || (strcmp(typeStr, "Natural Gamma") == 0) || (strcmp(typeStr, "All NaturalGamma") == 0) || (strcmp(typeStr, "NaturalGamma") == 0))
		coreType = NATURALGAMMA; 
	else if ((strcmp(typeStr, "All Reflectance") == 0) || (strcmp(typeStr, "Reflectance") == 0))
		coreType = REFLECTANCE; 
	else if ((strcmp(typeStr, "All OtherType") == 0) || (strcmp(typeStr, "OtherType") == 0))
		coreType = OTHERTYPE; 
	else if (strcmp(typeStr, "Log") == 0)
		coreType = LOGTYPE; 
	else if (strcmp(typeStr, "Spliced Records") == 0)
		coreType = SPLICE; 
	else
		coreType = USERDEFINEDTYPE;

	return coreType;
}

// 9/9/2013 brg
// Given typeStr, find matching integer type. If it's not a built-in type,
// set outAnnot = to typeStr. This logic is duplicated throughout py_func.cpp.
// I'm not in love with using parameters for output, but it's less offensive
// than the duplication by a long shot.
static bool getTypeAndAnnot(char *typeStr, int &outType, char **outAnnot)
{
	bool builtInType = false;
	outType = getType(typeStr);
	if (outType != USERDEFINEDTYPE)
	{
		*outAnnot = NULL;
		builtInType = true;
	}
	else
	{
		*outAnnot = typeStr;
	}

	return builtInType;
}
