//////////////////////////////////////////////////////////////////////////////////
// CorrelatorLib - Correlator Class Library.  
//
// Module   :  AutoCorrelator.cpp
// Author   :  Hyejung Hur
// Description: 
//
// Copyright (C) 2007 Hyejung Hur,  
// Electronic Visualization Laboratory, University of Illinois at Chicago
//
// This library is free software; you can redistribute it and/or modify it 
// under the terms of the GNU Lesser General Public License as published by
// the Free Software Foundation; either Version 2.1 of the License, or 
// (at your option) any later version.
//
// This library is distributed in the hope that it will be useful, but
// WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
// or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public 
// License for more details.
// 
// You should have received a copy of the GNU Lesser Public License along
// with this library; if not, write to the Free Software Foundation, Inc., 
// 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
//
// Direct questions, comments etc about Correlater Lib to hjhur@evl.uic.edu
//

#include <math.h>

#include <CoreTypes.h>
#include <AutoCorrelator.h>

#ifdef DEBUG
#include <iostream>
#endif

using namespace std;

AutoCorrResult::AutoCorrResult( void ) : m_coef(1.0f), m_squish(100.0f), m_offset(0.0f), m_rate(0), m_b(0), m_holeptrA(NULL), m_holeptrB(NULL) 
{ 
}

AutoCorrResult::AutoCorrResult( Hole* ahole, Hole* bhole, double coef, double rate, double b, double squish, double offset ) : 
m_coef(coef), m_squish(squish), m_offset(offset), m_rate(rate), m_b(b),  m_holeptrA(ahole), m_holeptrB(bhole) 
{ 
}

AutoCorrelator::AutoCorrelator( void ) :
 m_correlator(NULL), m_isReady(NO),
 m_squish_inc(0.0f), m_offset_inc(0.0f), m_isSplice(false),
 m_nsquish(1.0f), m_noffset(0.0f), m_valueptr(NULL),
 m_flip(1), m_noTiesinCore(0), m_coreStartNum(0), m_coreMaxNum(0)
{	
	m_range_squish[0] = m_range_squish[1] = 100.0f;
	m_range_offset[0] = m_range_offset[1] = 0.0f;
	m_coreptr[0] = NULL;
	m_coreptr[1] = NULL;
	m_mainHoleptr = NULL;
}

AutoCorrelator::AutoCorrelator( Correlator* ptr, int tiesinCore ) :
 m_correlator(ptr), m_isReady(NO),
 m_squish_inc(0.0f), m_offset_inc(0.0f),  m_isSplice(false),
 m_nsquish(1.0f), m_noffset(0.0f), m_valueptr(NULL), 
 m_flip(1), m_noTiesinCore(tiesinCore), m_coreStartNum(0), m_coreMaxNum(0)
{	
	m_range_squish[0] = m_range_squish[1] = 100.0f;
	m_range_offset[0] = m_range_offset[1] = 0.0f;

	m_coreptr[0] = NULL;
	m_coreptr[1] = NULL;
	m_mainHoleptr = NULL;

	for(int i=0; i < m_noTiesinCore; i++)
	{
		Tie* tieptr = new Tie(COMPOSITED_TIE);
		// tieptr->setApply(YES);
		m_ties.push_back(tieptr);
	}
}

AutoCorrelator::~AutoCorrelator( void )
{
	Tie* tieptr =  NULL;
	for(int i=0; i < m_noTiesinCore; i++)
	{
		tieptr = (Tie*) m_ties[i];
		delete tieptr;
		tieptr = NULL;
	}
	m_ties.clear();
}
	
void AutoCorrelator::init( void )
{
	m_holelist.clear();
	m_noTiesinCore = 0;
	m_valueptr = NULL;
	m_corelist.clear();
	m_isSplice = false;	
}
	
void AutoCorrelator::visitor( CoreObject* object )
{
}

int AutoCorrelator::correlate( void )
{	
	//std::cout << "correlate .... start " << std::endl;

	// check whether parameter is ready
	if(m_correlator == NULL) return -1;
	if(m_holelist.size() == 0) return -1;
	if(m_isReady == NO) return -1;
	//if(m_noTiesinCore <= 0) return -1;
		
	Hole* holeptrA = m_correlator->getLogData()->getHole(0);
	Hole* holeptrB = m_holelist[0]; // temporarily
#ifdef DEBUG	
	printf("log name : %s , selected name : %s\n", holeptrA->getName(), holeptrB->getName());
#endif
	
	double depstep = m_correlator->getDepthStep();
#ifdef DEBUG
	printf("depstep : %f \n", depstep);
#endif	
	//////// ??????????
	double nboxes = m_nsquish * m_noffset;
#ifdef DEBUG
	printf("nboxes : %f \n", nboxes);
#endif	
	int ret = 0;
	//double flip_off = holeptrB->getRange()->max - holeptrB->getRange()->min;
   
	m_result.clear();
	
	
	// RANGE
	double rangeA[2];
	double rangeB[2];
	double range[2];
		
	Core* coreptrA = NULL;
	Core* coreptrB = NULL;
	
	int numCore;
	double relativepos = 1.0f / m_noTiesinCore;

	//rangeA[0] = holeptrA->getRange()->mindepth;
	//rangeA[1] = holeptrA->getRange()->maxdepth;
	rangeA[0] = holeptrA->getRange()->top;
	rangeA[1] = holeptrA->getRange()->bottom;
	//printf("rangeA : %f, rangeA : %f \n", rangeA[0], rangeA[1]);
	

	rangeB[0] = holeptrB->getRange()->mindepth;
	rangeB[1] = holeptrB->getRange()->maxdepth;	
	//printf("rangeB : %f, rangeB : %f \n", rangeB[0], rangeB[1]);
		
	// calculate range
	// range0 == start, range1 == stop
	if(rangeA[0] < rangeB[0])
	{
		range[0] = rangeB[0];
	} else 
	{
		range[0] = rangeA[0];
	}
		
	if(rangeA[1] < rangeB[1])
	{
		range[1] = rangeA[1];
	} else 
	{
		range[1] = rangeB[1];
	}	
	//printf("start : %f, stop : %f \n", range[0], range[1]);
	
	 /*numCore = (range[1] - range[0]) / depstep;	
	printf("num core : %d\n", numCore);*/

	double fsquish, foffset;
	int    count=0;
	double coef=0.0f;	
	
	// m_depth_step
		
	coreptrA = holeptrA->getCore(0);
	coreptrB = holeptrB->getCore(range[0], depstep);
	if(coreptrA == NULL || coreptrB == NULL) return -1;
	
	// log has one core
	int coreNo = coreptrB->getNumber();
	//printf("coreNo : %d \n", coreptrB->getNumber());
	int startcore_num = coreNo;
	
	int coremax = holeptrB->getNumOfCores() - coreNo;	
	
	numCore = coremax;
	//printf("num core : %d\n", numCore);

	double rate;
	double b;
	double totalrate;
	double totalb;
	double tempcoef;
	m_valueptr = NULL;

	// squish
	for(fsquish =  m_range_squish[0]; fsquish >= m_range_squish[1]; fsquish -= m_squish_inc)
	{
		// offset
		for(foffset = m_range_offset[0]; foffset <= m_range_offset[1]; foffset += m_offset_inc)
		{
			//printf("squish : %f, offset : %f, numCore : %d\n", fsquish, foffset, numCore);
			coef = 0.0f;
			count = 0;
			totalrate = 0;
			totalb = 0;	
			coreNo = startcore_num;
			coreNo++;
			coreptrB = holeptrB->getCoreByNo(coreNo);
			//std::cout << "correlate  1 : " << coreptrB->getName() << coreptrB->getNumber() << std::endl;

						
		
			for(int i=0; i < numCore; i++) 
			{
				if(coreptrB == NULL) continue;
				//std::cout << "core -> " << coreptrB->getName()  << coreptrB->getNumber() << std::endl;
				tempcoef = evalCore(coreptrA, coreptrB, fsquish, foffset, rate, b);	
				coef += tempcoef;
				count++;
				totalrate += rate;
				totalb += b;
				coreNo++;
				coreptrB = holeptrB->getCoreByNo(coreNo);
				//std::cout << "> correlate  1 : " << coreptrB->getName() << coreptrB->getNumber() << std::endl;

				
			}	// end of for statement : isquish
			coef = coef / count;
			totalrate = totalrate / count;
			//totalb = totalb / count;
			m_result.push_back(AutoCorrResult(holeptrA, holeptrB, coef, totalrate, totalb, fsquish, foffset));
			//cout << "COEF : " << coef << count << endl;
		}
	}	// end of for statement : ioffset 
		

	////////////////////////
	// analysis result
	double max_coef = -999.0f;
	vector<AutoCorrResult>::iterator iterResult;
	AutoCorrResult result;
	for(iterResult = m_result.begin(); iterResult != m_result.end(); iterResult++)
	{
		result = (AutoCorrResult) *iterResult;
		if(max_coef < result.m_coef)
		{
			max_coef = result.m_coef;
			m_best_result.m_squish =  result.m_squish;
			m_best_result.m_offset = result.m_offset;
			m_best_result.m_coef = result.m_coef;
			m_best_result.m_rate = result.m_rate;
			m_best_result.m_b = result.m_b;
		}
#ifdef DEBUG		
		cout << " isquish " << result.m_squish << " offset " << result.m_offset << " coef : " << result.m_coef  << " rate : " << result.m_rate << " b : " << result.m_b << endl;
#endif
	}
#ifdef DEBUG
	cout << " BEST :  squish " << m_best_result.m_squish << " offset " << m_best_result.m_offset << " coef : " << m_best_result.m_coef <<  " rate : " << m_best_result.m_rate << " b : " << m_best_result.m_b << endl;
#endif
	
	return 1;
}


int AutoCorrelator::correlate( double squish, double offset, double& ret_rate, double& ret_b )
{
	if(m_coreptr[0] == NULL || 	m_coreptr[1] == NULL) return -1;

	m_coreptr[0]->initDepthOffset();
	m_coreptr[0]->setDepthOffset(offset, true);
	m_coreptr[0]->updateLight();

	double rate;
	double b;
	double tempcoef;

	//printf("squish : %f, offset : %f, numCore : %d\n", squish, offset, numCore);
	double coef = 0.0f;
	int count = 0;
	double totalrate = 0.0;
	double totalb = 0.0;	
	int coreNo = m_coreStartNum;
	Core* coreptrB = m_coreptr[1];
	//std::cout << "correlate  2 : " << coreptrB->getName() << coreptrB->getNumber() << std::endl;


	//cout << "m_coreMaxNum : " << m_coreMaxNum << endl;
	Hole* holeptr = NULL;
	Core* coreptr = NULL;
	int index =0;
	m_valueptr = NULL;
	
	//cout << "m_holelist size : " << m_holelist.size() << endl;
	//cout << " ======================================================  " << m_depth_step << endl;
	
	for(vector<Hole*>::iterator iter= m_holelist.begin(); iter != m_holelist.end(); iter++, index++)
	{
		holeptr = (Hole*) * iter;
		if(holeptr == NULL) continue;
		coreptrB = m_corelist[index];
		if(coreptrB == NULL) continue;
		coreNo = coreptrB->getNumber();		
		for(int i=0; i < m_coreMaxNum; i++) 
		{
			if(coreptrB == NULL) continue;
			//cout << coreptrB->getName() << coreptrB->getNumber() << endl;
			
			tempcoef = evalCore(m_coreptr[0], coreptrB, squish, 0, rate, b);	
			coef += tempcoef;
			count++;
			totalrate += rate;
			totalb += b;
			coreNo++;
			coreptrB = holeptr->getCoreByNo(coreNo);
		}	// end of for statement : isquish
		
	}
	
	coef = coef / count;
	totalrate = totalrate / count;
	ret_rate = totalrate;
	ret_b = totalb;
	
	if(index > 0)
		ret_b /= index;

	//cout << "ret_rate : " << totalrate << " ret_b :"  << ret_b << " count :" << count << endl;
		
	return 1;
}
	

int AutoCorrelator::applyBest( void )
{
	int ret = apply(m_best_result.m_offset, m_best_result.m_squish, m_best_result.m_offset);	
	return ret;
}

int  AutoCorrelator::apply(  double stretch, double mudline )
{
	//cout << "stretch = " << stretch << " mudline = " << mudline << endl;
	apply(0.0, 100, 0, false);
	return 	apply(mudline, stretch, mudline);
}	

int AutoCorrelator::applyBestToAll( void )
{
	return 	applyToAll(m_best_result.m_offset, m_best_result.m_squish, m_best_result.m_offset);
}

int  AutoCorrelator::applyToAll(  double stretch, double mudline )
{
	//cout << "stretch = " << stretch << " mudline = " << mudline << endl;
	return 	applyToAll(mudline, stretch, mudline);
}	

int AutoCorrelator::applyToAll( void )
{
	if(m_correlator == NULL) return 0;
	Data* dataptr = m_correlator->getDataPtr();
	if(dataptr == NULL) return 0;
	
	int ret = 0;
	if(dataptr->getCorrStatus() == YES)
	{
		double stretch = dataptr->getStretch();
		double mudline = dataptr->getMudLine();
		ret = applyToAll(mudline, stretch, mudline);
	}
	return ret;
}

int AutoCorrelator::undo( void )
{
	return apply(0.0, 100, 0, false);
	//return apply(-m_best_result.m_offset, 100, 0, false);
}

int AutoCorrelator::undoToAll( void )
{
	apply(0.0, 100, 0, false);
	return applyToAll(0.0, 100, 0, false);
	//return applyToAll(-m_best_result.m_offset, 100, 0, false);
}

int AutoCorrelator::apply( double appliedOffset, double stretch, double mudline, bool doflag )
{
	if(m_correlator->getLogData() != NULL)
	{
		Hole* holeptrA = m_correlator->getLogData()->getHole(0);
		if(holeptrA == NULL) return 0;
		Core* coreptrA = holeptrA->getCore(0);
		if(coreptrA == NULL) return 0;
		if (appliedOffset == 0.0) 
			coreptrA->initDepthOffset();
		else 
			coreptrA->setDepthOffset(appliedOffset, true);
		coreptrA->update();
	}
	
	//Hole* holeptrB = m_holelist[0]; // temporarily
	Hole* holeptrB = NULL;
	Core* coreptrB = NULL;	
	int coremax = 0;
	if(m_isSplice == false)
	{
		for(vector<Hole*>::iterator iter= m_holelist.begin(); iter != m_holelist.end(); iter++)
		{
			holeptrB = (Hole*) * iter;
			if(holeptrB == NULL) return 0;
			if(holeptrB->getELDStatus() == doflag) return 0;
				
			coremax = holeptrB->getNumOfCores();	
			for(int i=0; i < coremax; i++) 
			{
				coreptrB = holeptrB->getCore(i);
				if(coreptrB == NULL) continue;
				coreptrB->setStretch(stretch);
			}
			holeptrB->setELDStatus(doflag);	
			holeptrB->update();
		}
	}
	else {
		////
		int size =  m_correlator->getDataPtr()->getNumOfHoles();
		for(int i=0; i < size; i++)
		{
			holeptrB = m_correlator->getDataPtr()->getHole(i);
			if(holeptrB == NULL) return 0;
			if(holeptrB->getELDStatus() == doflag) return 0;
				
			coremax = holeptrB->getNumOfCores();	
			for(int i=0; i < coremax; i++) 
			{
				coreptrB = holeptrB->getCore(i);
				if(coreptrB == NULL) continue;
				coreptrB->setStretch(stretch);
			}
			holeptrB->setELDStatus(doflag);	
			holeptrB->update();
		}
		/////
	}
			
	
	//m_correlater->getDataPtr()->setStretch(stretch);
	//m_correlater->getDataPtr()->setMudLine(mudline);	
	return 1;
}

int AutoCorrelator::applyToAll( double appliedOffset, double stretch, double mudline, bool doflag )
{
	if(m_correlator == NULL) return 0;

	if(m_correlator->getLogData() != NULL)
	{
		Hole* holeptrA = m_correlator->getLogData()->getHole(0);
		if(holeptrA == NULL) return 0;
		Core* coreptrA = holeptrA->getCore(0);
		if(coreptrA == NULL) return 0;
		if (appliedOffset == 0.0) 
			coreptrA->initDepthOffset();
		else 
			coreptrA->setDepthOffset(appliedOffset, true);
		coreptrA->update();
	}

	Data* dataptr = m_correlator->getDataPtr();
	if(dataptr == NULL) return 0;

	int numHoles = dataptr->getNumOfHoles();
	int numCores;
	
    Hole* holeptr;
    Core* coreptr;		
	//double offset;
	for(int i=0; i < numHoles; i++)
	{
		holeptr = dataptr->getHole(i);
        if (holeptr == NULL) continue;
		if(holeptr->getELDStatus() == doflag) continue;
		
        numCores =  holeptr->getNumOfCores();
        for(int j=0; j <= numCores; j++)
        {
			coreptr = holeptr->getCore(j);
            if (coreptr == NULL) continue;

			//offset = coreptr->getDepthOffset() - appliedOffset;
			//coreptr->setDepthOffset(offset, true);
			coreptr->setStretch(stretch);
		}
		holeptr->setELDStatus(doflag);
	}
	dataptr->setStretch(stretch);
	dataptr->setMudLine(mudline);
	
	return 1;
}

double	AutoCorrelator::evalCore( Core* coreA, Core* coreB, double squish, double offset, double& rate, double& b)
{
	double eval = 0.0f;
	double squish_rate = squish / 100.0f;	
	
	// find start value
	double top = coreB->getRange()->mindepth;
	
	double avedepstep = coreB->getRange()->avedepstep;
	int indexgap = (int) (round(m_depth_step / avedepstep));
	//cout << "m_depth_step : " << m_depth_step << " , " << avedepstep << " indexgap : " << indexgap << endl;
	
	double logdepstep = coreA->getRange()->avedepstep ;
	int logindexgap = (int) (round(m_depth_step / logdepstep));
	//cout << "logdepstep : " << logdepstep << " logindexgap : " << logindexgap << endl;
	
	if(m_valueptr == NULL)
	{
		m_valueptr = m_correlator->findValue(coreA, (top - offset) * squish_rate);
	} else {
		m_valueptr = findValue(coreA, m_valueptr, (top - offset) * squish_rate);
	}
	
	Value* valueB = coreB->getValue(0);
	
	if(m_valueptr == NULL || valueB == NULL) return eval;

	//cout << m_valueptr->getELD() <<  " : " << valueB->getELD()  << " --- " << coreB->getName() << coreB->getNumber() << " " << squish << " " << offset << endl;
	
	eval = evalCore(coreA, coreB, m_valueptr, valueB, squish_rate, offset, indexgap, logindexgap, b);
	
	rate = eval;
	//printf("mbsf : (%f , %f), mcd : (%f, %f), rate : %f, b : %f eval : %f \n", valueA->getMbsf(), valueB->getMbsf(),  tempdepth[1],  tempdepth[0], rate, b, eval);
	return eval;
}


double AutoCorrelator::evalCore( Core* coreA, Core* coreB, Value* valueA, Value* valueB, double squish, double offset, int indexgap, int logindexgap, double& bnum )
{
    //  sum up
	int n = coreA->getNumOfValues() -1;
    int nY = coreB->getNumOfValues() -1;
			
	int a = valueA->getNumber();
	int b = valueB->getNumber();

	int end = nY-b; 


	//double squish_rate = squish / 100.0f;	
	
	//cout << coreA->getName() << ", index : " << valueA->getNumber() << ", value : " << valueA->getELD() << 
	//	    coreB->getName() << ", index : " << valueB->getNumber() << ", value : " << valueB->getELD() << " : end : " <<  end << endl;

	///////////////////////////////
	// find start and end

	///////////////////////////////
	// calculate coef
	double sumX = 0.0;
	double sumXsq = 0.0;
	double sumY = 0.0;
	double sumYsq = 0.0;
	double sumXY = 0.0;

	int nx = 0;
	double valueX, valueY;
	b -= indexgap;
	
	double expectedDepthX =0.0f, depthX, depthY, prevValueX, prevDepthX=0.0f;
	Value* valueAptr = NULL;
	Value* valueBptr = NULL;		
	
	valueAptr = coreA->getValue(a);
	if(valueAptr != NULL) 
	{
		valueX = valueAptr->getData();
		depthX = valueAptr->getELD();	
	}
	
	double depth_step = m_depth_step * squish;
	double rate = 0;

	int i = 0;
	for(i = 0; i <= end; i++)
	{
		b += indexgap;	
		if (b >  nY) break;
		valueBptr = coreB->getValue(b);
		if(valueBptr == NULL) continue;
		valueY = valueBptr->getData();
		depthY = valueBptr->getELD();
		depthY  = (depthY - offset) * squish;
		
		if(i > 0)
		{
			expectedDepthX = depthY;
			
			if(expectedDepthX <= depthX)
			{
				rate = (valueX - prevValueX) / (depthX - prevDepthX);
				valueX = rate * expectedDepthX  - prevDepthX * rate + prevValueX;
			} else 
			{
				prevValueX = valueX;
				prevDepthX = depthX;
				
				a += logindexgap;	
				if (a >  n) break;
				valueAptr = coreA->getValue(a);
				if(valueAptr == NULL) continue;
				valueX = valueAptr->getData();
				depthX = valueAptr->getELD();

				rate = (valueX - prevValueX) / (depthX - prevDepthX);
				valueX = rate * expectedDepthX  - prevDepthX * rate + prevValueX;
			} 
			depthX = expectedDepthX;					
			
		} else 
		{
			prevValueX = valueX;
			prevDepthX = depthX;
	
			a += logindexgap;	
			if (a >  n) break;
			valueAptr = coreA->getValue(a);
			if(valueAptr == NULL) continue;
			valueX = valueAptr->getData();
			depthX = valueAptr->getELD();			
		}
		
		//cout << "valueX : " << coreA->getValue(a)->getMcd() << ", valueY : " << coreB->getValue(b)->getMcd()  <<  endl;
		//cout << "valueX : " << valueX << ", valueY : " << valueY  << ", squish_rate : " << squish_rate <<  endl;

		if(valueAptr->getQuality() != BAD_PT || valueBptr->getQuality() != BAD_PT)
		{
				sumX = sumX + valueX;
				sumXsq = sumXsq + (valueX * valueX);
				sumY = sumY + valueY;
				sumYsq = sumYsq + (valueY * valueY);
				sumXY =  sumXY + (valueX * valueY);
				nx++;
		}
	}

	//cout << "end = " << i << endl;


	bnum = nx;
	// calculate the standard deviation and the correlation coefficient
	double coef =0.0;
	double stdevX, stdevY;
	if(nx > 1)
	{
			stdevX = (nx * sumXsq) - (sumX * sumX);
			stdevY = (nx * sumYsq) - (sumY * sumY);

			if(stdevX <= 0 || stdevY <= 0)
			{
					coef=0.0;
					return 0;
			} else
			{

					stdevX = sqrt(stdevX);
					stdevY = sqrt(stdevY);
					coef = ((nx * sumXY) - (sumX * sumY)) / (stdevX * stdevY);
			}
	} else
	{
			coef=0.0;
	}

	return coef;
}

Value* AutoCorrelator::findValue( Core* coreptr, Value* valueptr, double top )
{
	if(coreptr == NULL) return NULL;
	// find value
 	int size = coreptr->getNumOfValues();
	double valueX, valueY;
	int ret =0, i;
	int left = size % 2;
	size--;
	if(left == 1) 
	{
		size--;
	}	

	double topgabX, topgabY;	
	Value* valueptrA = NULL;
	Value* valueptrB = NULL;
	for(i=valueptr->getNumber() ; i < size; i++) 
	{
		//valueX = coreptr->getValue(i)->getTop();
		//valueY = coreptr->getValue(i+1)->getTop();
		
		valueptrA = coreptr->getValue(i);
		valueptrB = coreptr->getValue(i+1);
		if(valueptrA == NULL || valueptrB == NULL) continue;
		valueX = valueptrA->getELD();
		valueY = valueptrB->getELD();
		
		topgabX =  top -  valueX;
		topgabY = top - valueY;

		//cout << "value x : " << valueX << " , " << valueY << " :" << top << " ---" << topgabX << "," <<topgabY << endl;
	
		if((topgabX >= -0.01) && (topgabY < 0.00)) 	//if((top >= valueX) && (top <= valueY))
		{
			//cout << "value x : " << valueX << " , " << valueY << " :" << top << " ---" << topgabX << "," <<topgabY << endl;
			ret = 1;
			break;
		}
		if(valueX == top) 
		{
			ret = 1;
			break;
		}
	} 	 
	if(left == 1)
	{
		valueX = valueY;
		//valueY = coreptr->getValue(i)->getTop();
		//valueY = coreptr->getValue(i)->getELD();

		valueptrB = coreptr->getValue(i);
		if(valueptrB != NULL) 
		{	
			valueY = valueptrB->getELD();
			topgabX =  top -  valueX;
			topgabY = top - valueY;
			if((topgabX >= -0.01) && (topgabY <= 0.01))	//if((top >= valueX) && (top <= valueY))
			{
				ret = 1;
			}
			if(valueX == top) 
			{
				ret = 1;
			}			
		}
	}
	if(ret == 1)
	{
		//cout << "found " << endl;
		return coreptr->getValue(i);
	}
	
	return NULL;
	
}
	
int AutoCorrelator::correlate_backup( void )
{
	if(m_correlator == NULL) return -1;
	if(m_isReady == NO) return -1;

	double depstep = m_correlator->getDepthStep();

	double nboxes = m_nsquish * m_noffset;

	int ret = 0;

	Data* dataptr = m_correlator->getDataPtr();
	if(dataptr == NULL) return -1;
	double flip_off = dataptr->getRange()->max - dataptr->getRange()->min;
   
	m_result.clear();
	
	int noholes = m_holes.size();
	if(noholes < 2) return -1;
	int count = noholes / 2;
	
	string name;
	Hole* holeptrA;
	Hole* holeptrB;
	double rangeA[2];
	double rangeB[2];
	double range[2];	
	Core* coreptrA;
	Core* coreptrB;
	int numCore;
	Tie* tieptr;
	double relativepos = 1.0f / m_noTiesinCore;
	vector<Tie*>::iterator tie_index;
	double coef;
	
	for(int i=0; i < count; i++)
	{
	
		name = m_holes[i];
		holeptrA = dataptr->getHole((char*)name.c_str());
		if(holeptrA == NULL) continue;
		rangeA[0] = holeptrA->getRange()->mindepth;
		rangeA[1] = holeptrA->getRange()->maxdepth;
				
		name = m_holes[i+1];
		holeptrB = dataptr->getHole((char*)name.c_str());
		if(holeptrB == NULL) continue;		
		rangeB[0] = holeptrB->getRange()->mindepth;
		rangeB[1] = holeptrB->getRange()->maxdepth;	
		
		// calculate range
		if(rangeA[0] < rangeB[0])
		{
			range[0] = rangeA[0];
		} else 
		{
			range[0] = rangeB[0];
		}
		
		if(rangeA[1] < rangeB[1])
		{
			range[1] = rangeA[1];
		} else 
		{
			range[1] = rangeB[1];
		}	

		// find core in the range
		// find how many cores....
		//numCoreA = holeptrA->getNumOfCores(range[0], range[1]);
		//numCoreB = holeptrB->getNumOfCores(range[0], range[1]);
		// todo
		numCore = (range[1] - range[0]) / depstep;
		for(int j=0; j < numCore; j++) 
		{
			coreptrA = holeptrA->getCore(range[0], depstep);
			coreptrB = holeptrB->getCore(range[0], depstep);
			range[0] += depstep;
			if(coreptrA == NULL || coreptrB == NULL) continue;
		
			for(double isquish =  m_range_squish[0]; isquish >= m_range_squish[1]; isquish -= m_squish_inc)
			{
				// offset
				for(double ioffset = m_range_offset[0]; ioffset <= m_range_offset[1]; ioffset += m_offset_inc)
				{
					coef = 0.0f;
					for(tie_index = m_ties.begin(); tie_index != m_ties.end(); tie_index++)
					{
						tieptr = (Tie*) *tie_index;
						ret = updateTie(tieptr, coreptrA, relativepos, coreptrB, relativepos );
						if(ret <= 0) continue;
						
						// squish
						tieptr->setStretch(isquish);
						
						// offset
						tieptr->applyAffine(ioffset);
						
						// update
						tieptr->calcCoefficientUpdate();

						// get coef
						coef += tieptr->getCoef();
						
					}
					coef = coef / m_noTiesinCore;
					//m_result.push_back(AutoCorrResult(coreptrA, coreptrB, coef, isquish, ioffset));
	
				} // end of for statement : ioffset 
			} // end of for statement : isquish
		} // end of for statement : numcore-j
	} // end of for statement : numholes
	
	// analysis result
	vector<AutoCorrResult>::iterator iterResult;
	AutoCorrResult result;
	for(iterResult = m_result.begin(); iterResult != m_result.end(); iterResult++)
	{
		result = (AutoCorrResult) *iterResult;
#ifdef DEBUG		
		cout << "coef : " << result.m_coef  << " isquish " << result.m_squish << " offset " << result.m_offset << endl;
#endif
	}

	return 1;
}

int AutoCorrelator::updateTie( Tie* tieptr, Core* coreA, double relativeposA, Core* coreB, double relativeposB )
{
	if(tieptr == NULL) return -1;
	
	// find coreA and coreB
	if(coreA == NULL || coreB == NULL) return -1;
	
	// calculate all inforamtion : top/bottom...
	// top, bottom
	data_range rangeA, rangeB;
	rangeA.top = (coreA->getBottom() - coreA->getTop()) * relativeposA;
	rangeA.bottom = rangeA.top;
	rangeB.top = (coreB->getBottom() - coreB->getTop()) * relativeposB;
	rangeB.bottom = rangeB.top;
	
	// find value.....
	Value* valueA = m_correlator->findValue(coreA, rangeA.top);
	Value* valueB = m_correlator->findValue(coreB, rangeB.top);
	if(valueA == NULL || valueB == NULL) return -1;
		
	// create Tie and register.......
	tieptr->setTied(coreA, valueA->getType(), valueA->getSection(), rangeA);
	tieptr->setTieTo(coreB, valueB->getType(), valueB->getSection(), rangeB);
	
	return 1;
}

int AutoCorrelator::setCorrelate( void )
{
	// check whether parameter is ready
	if(m_correlator == NULL) return -1;
	if(m_holelist.size() == 0) return -1;
	if(m_isReady == NO) return -1;
	//if(m_noTiesinCore <= 0) return -1;

	undoToAll();

	m_coreptr[0] = NULL;
	m_coreptr[1] = NULL;
	m_mainHoleptr = NULL;
	m_coreStartNum = 0;
	m_coreMaxNum = 0;		
		
	Hole* holeptrA = m_correlator->getLogData()->getHole(0);

	int index = m_holelist.size();
	Hole* holeptrB = m_holelist[0]; 
	m_mainHoleptr = holeptrB;
	//printf("log name : %s , selected name : %s, size : %d\n", holeptrA->getName(), holeptrB->getName(), index);
	
	double depstep = m_correlator->getDepthStep();
	
	//////// ??????????
	double nboxes = m_nsquish * m_noffset;
	//printf("nboxes : %f \n", nboxes);
	
	int ret = 0;
	//double flip_off = holeptrB->getRange()->max - holeptrB->getRange()->min;
   
	// RANGE
	double rangeA[2];
	double rangeB[2];
	double range[2];
		
	Core* coreptrA = NULL;
	Core* coreptrB = NULL;
	
	double relativepos = 1.0f / m_noTiesinCore;

	rangeA[0] = holeptrA->getRange()->mindepth;
	rangeA[1] = holeptrA->getRange()->maxdepth;
	//rangeA[0] = holeptrA->getRange()->top;
	//rangeA[1] = holeptrA->getRange()->bottom;
	//printf("log rangeA : %f, rangeA : %f  %d\n", rangeA[0], rangeA[1], holeptrA->getNumOfCores());

	//std::cout << holeptrB->getName() <<  holeptrB->getNumOfCores() << endl;
	rangeB[0] = holeptrB->getRange()->mindepth;
	rangeB[1] = holeptrB->getRange()->maxdepth;	

	if(m_isSplice == false)
	{
		if(m_holelist.size() > 1)
		{
			Data* dataptr = m_correlator->getDataPtr();
			Hole* holeptr = NULL;
			double rangeTemp[2];
			int holes = dataptr->getNumOfHoles();
			for(int i = 1; i < holes; i++)
			{
				holeptr = dataptr->getHole(i);
				if(holeptr == NULL) continue;
				rangeTemp[0] = holeptr->getRange()->mindepth;
				rangeTemp[1] = holeptr->getRange()->maxdepth;
				if(rangeB[0] < rangeTemp[0])
					rangeB[0] = rangeTemp[0];
				if(rangeB[1] > rangeTemp[1])
					rangeB[1] = rangeTemp[1];
			}
		}
	} else 
	{
		data_range* range_temp = holeptrA->getRange();
	
		int max = holeptrB->getNumOfCores()-1;
		Core* coreptr_temp = holeptrB->getCore(max);
		if(coreptr_temp) 
		{
			range_temp->maxdepth = coreptr_temp->getRange()->maxdepth;
			rangeB[1] = range_temp->maxdepth;	
		}
	}
	//printf("rangeB : %f, rangeB : %f\n", rangeB[0], rangeB[1]);


	//std::cout << rangeA[0] << " " << rangeB[0] << " : " <<  rangeA[1] << " " << rangeB[1] << std::endl;
	
	// calculate range
	// range0 == start, range1 == stop
	if(rangeA[0] < rangeB[0])
	{
		range[0] = rangeB[0];
	} else 
	{
		range[0] = rangeA[0];
	}
		
	if(rangeA[1] < rangeB[1])
	{
		range[1] = rangeA[1];
	} else 
	{
		range[1] = rangeB[1];
	}	
#ifdef DEBUG	
	printf("[AutoCorrelater] start : %f, stop : %f \n", range[0], range[1]);
#endif	
	m_coreptr[0] = holeptrA->getCore(0);
	m_coreptr[1] = holeptrB->getCore(range[0], depstep);
	if(m_coreptr[0] == NULL || m_coreptr[1] == NULL) return -1;

	
	//std::cout << " setCorrelate >> ------------ " << range[0] << " " << depstep << " " << m_coreptr[1]->getName() << m_coreptr[1]->getNumber() << std::endl;
	m_coreptr[0]->initDepthOffset();
	m_coreptr[0]->update();
		
	m_coreStartNum = m_coreptr[1]->getNumber()+1;

	Core* coreptr = NULL;
	if(m_isSplice == false)
	{
		coreptr = holeptrB->getCore(range[1], depstep);
		if(coreptr == NULL) 
		{
			coreptr = holeptrB->getCore(holeptrB->getNumOfCores() -1);
		}
		m_coreMaxNum = coreptr->getNumber();
#ifdef DEBUG		
		cout << "[AutoCorrelater] start : " << m_coreStartNum << " stop : " << m_coreMaxNum << endl;
#endif
	} else 
	{
		m_coreMaxNum = holeptrB->getNumOfCores() - m_coreStartNum;	
#ifdef DEBUG
		cout << "[AutoCorrelater] start : " << m_coreStartNum << " stop : " << m_coreMaxNum + m_coreStartNum << endl;
#endif
	}

	m_coreptr[1] = holeptrB->getCoreByNo(m_coreStartNum);
	m_corelist.push_back(m_coreptr[1]);

	if(index > 1)
	{
		vector<Hole*>::iterator iter = m_holelist.begin();
		iter++;
		Hole* holeptr;
		for(; iter != m_holelist.end(); iter++)
		{
			holeptr = (Hole*) *iter;
			if(holeptr == NULL) continue;
			coreptr = holeptr->getCore(m_coreptr[1]->getRange()->mindepth, 0);
			m_corelist.push_back(coreptr);
		} 
	}
	//cout << "---------" << endl;
		
	return 1;
}
	
void AutoCorrelator::setSquishRange( double from, double to, double inc )
{
	/*if(from == to) 
	{
		m_isReady = NO;
		return;
	}*/
	if(from <= 0.0 || to <= 0.0) 
	{
		m_isReady = NO;
		return;
	}	
	if(inc <= 0.0) 
	{
		m_isReady = NO;
		return;
	}
		
	if(from < to)
	{
		m_range_squish[0] = to;
		m_range_squish[1] = from;
	} else 
	{
		m_range_squish[0] = from;
		m_range_squish[1] = to;
	}
	m_squish_inc = inc;
	m_isReady = YES;
}

void AutoCorrelator::setOffsetRange( double from, double to, double inc )
{
	if(from == -0.0f) from = 0.0f;
	if(to == -0.0f) to = 0.0f;
	if(from == to) 
	{
		m_isReady = NO;
		return;
	}
	/*if(from <= 0.0 || to <= 0.0) 
	{
		m_isReady = NO;
		return;
	}*/	
	if(inc <= 0.0) 
	{
		m_isReady = NO;
		return;
	}
			
	if(from < to)
	{
		m_range_offset[0] = from;
		m_range_offset[1] = to;
	} else 
	{
		m_range_offset[0] = to;
		m_range_offset[1] = from;
	}
	m_offset_inc = inc;
	m_isReady = YES;	
}
	
AutoCorrResult* AutoCorrelator::getBestCorrelate( void )
{
	return &m_best_result;
}

void AutoCorrelator::setDepthStep( double depthstep )
{
	m_depth_step = depthstep;
}

void AutoCorrelator::setCorrelator( Correlator* ptr )
{
	m_correlator = ptr;
}

void AutoCorrelator::setFlip( int flip )
{
	m_flip = flip;
}

void AutoCorrelator::setTiesNo( int tiesinCore )
{
	if(m_ties.size() >= tiesinCore) 
		m_noTiesinCore = tiesinCore;
	else 
	{
		int gab = tiesinCore - m_noTiesinCore; 
		Tie* tieptr = NULL;
		for(int i=0; i < gab; i++)
		{
			tieptr = new Tie(COMPOSITED_TIE);
			// tieptr->setApply(YES);
			m_ties.push_back(tieptr);
		}	
	}
}
	
void AutoCorrelator::addHole( char* holeName, int coretype, char* annotation )
{
	string str_name = holeName;

	Hole* holeptr = m_correlator->getDataPtr()->getHole(holeName, coretype, annotation);
	if(holeptr != NULL) 
	{
		m_holelist.push_back(holeptr);		
		m_holes.push_back(str_name);
#ifdef DEBUG		
		cout << "[AutoCorrelater] hole name : " << holeName  << endl;
#endif
	}
}

void AutoCorrelator::addHole( Hole* holeptr )
{
	if(holeptr != NULL)
	{
		m_holelist.push_back(holeptr);
#ifdef DEBUG		
		cout << "[AutoCorrelater] addHole holeName : " << holeptr->getName() << endl;	
#endif
		m_isSplice = true;
	}
}


void AutoCorrelator::clearHoles()
{
	m_holes.clear();
}

