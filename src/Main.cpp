#if defined(WIN32) || defined (linux)
#include <Python.h>
#else 
#include <Python/Python.h>
#endif

#include <iostream>
#include "DataManager.h"
#include "CullFilter.h"
#include "DecimateFilter.h"
#include "GaussianFilter.h"
#include "Correlater.h"
#include "AutoCorrelater.h"

int main(int argc, char** argv)
{
	if(argc < 2) return 0;

	Py_Initialize();
	PyObject *pName, *pModule, *pDict, *pFunc;
	PyRun_SimpleString("from time import time,ctime\n"
        		"print 'Today is',ctime(time())\n");


	/*
	FILE* pPyFile;
	pPyFile = fopen("../app/canvas.py","r+");
	if(pPyFile == NULL) {
		std::cout << "could not open the file" << std::endl; 
		return -1;
	}
	PyRun_SimpleFile(pPyFile, "../app/canvas.py");
	*/

	DataManager manager;
	manager.registerPath("../DATA/current-test");
	//manager.printPaths();

	Data* dataptr = NULL;
	for(int i = 1; i < argc; i++) 
	{
		dataptr = manager.load(argv[i], dataptr);
	}	
	
	if(dataptr)
	{
		// order : culling -> smoothing -> decimate
		/*CullFilter culling(10);
		dataptr->accept(&culling);
		DecimateFilter decimate(2);
		dataptr->accept(&decimate);
		GaussianFilter smoothing;
		dataptr->accept(&smoothing);*/
		Correlater correlater(dataptr); 
		AutoCorrelater autocorr(&correlater, 10);
	
		int count =0;
	
		// for example
		bool exit_flag = false;
		while(!exit_flag) {
		
			dataptr->update();
			if(count == 5) 
			{
				//correlater.splice(2, 0.5, 2996, 0.6);
				//correlater.composite(2, 0.5, 2996, 0.6);
				//correlater.composite(8580, 2, 0.7, 2996, 0.9);
				// correlater.squish(2, 95);
						
				autocorr.addHole('A');
				autocorr.addHole('B');
				autocorr.setSquishRange(90, 100, 1);
				autocorr.setOffsetRange(1, 10.0, 1);
				autocorr.correlate();
			}
#ifdef DEBUG			
			count++;
			if(count == 10) break;
#endif			
		}
				
#ifdef DEBUG
		dataptr->debugPrintOut();
		correlater.debugPrintOut();
#endif
	}
	
	if(dataptr) 
	{
		delete dataptr;
		dataptr = NULL;
	}

	Py_Finalize();
	
	return 1;
}
