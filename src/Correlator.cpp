//////////////////////////////////////////////////////////////////////////////////
// CorrelatorLib - Correlator Class Library.   
//
// Module   :  Correlator.cpp
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
#include <Correlator.h>

#include <Tie.h>
#include <Strat.h>
#include <Value.h>

#ifdef DEBUG
#include <iostream>
#endif

using namespace std;

Correlator::Correlator( void ) :
  m_dataptr(NULL), m_logdataptr(NULL), m_belowflag(false), m_tiepoint(NULL), 
  m_spliceType(CONSTRAINED), m_depthstep(0.11f),  m_isCoreOnly(true), m_sagan_corename(""),
  m_winlen(2.0f), m_leadlagmeters(2.0f), m_spliceOrder(0), m_givenCore(NULL), m_floating(false)
{	
	m_mainHole[0] = NULL;
	m_mainHole[1] = NULL;
}

Correlator::Correlator( Data* dataptr ) :
  m_dataptr(dataptr), m_logdataptr(NULL), m_belowflag(false), m_tiepoint(NULL),
  m_spliceType(CONSTRAINED), m_depthstep(0.11f), m_isCoreOnly(true), m_sagan_corename(""),
  m_winlen(2.0f), m_leadlagmeters(2.0f), m_spliceOrder(0), m_givenCore(NULL), m_floating(false)
{	
	m_mainHole[0] = NULL;
	m_mainHole[1] = NULL;
		
	if(m_dataptr)
	{
		m_correlatorData.setSite((char*)m_dataptr->getSite());
		m_correlatorData.setLeg((char*)m_dataptr->getLeg());
	}
}

Correlator::~Correlator( void )
{
	m_dataptr = NULL;
	init();
}

void Correlator::init( int type )
{
	// delete m_splicerholes
	vector<Hole*>::iterator iter;
	Hole* tempHole = NULL;
	for(iter = m_splicerholes.begin(); iter != m_splicerholes.end(); iter++) 
	{
		tempHole = (Hole*) *iter;
		if(tempHole) 
		{
			delete tempHole;
			tempHole = NULL;
		}
	}
	m_splicerholes.clear();	
	m_mainHole[0] = NULL;
	m_mainHole[1] = NULL;	
	m_spliceOrder = 0;
	m_tiepoint = NULL;
	m_givenCore = NULL;
	m_sagan_corename = "";
	m_floating = false;

	m_ties.clear();
	m_saganties.clear();
	m_sagantotalties.clear();
	m_coeflist.clear();
	m_splicerties.clear();
	
	generateSpliceHole();
	if(m_mainHole[0])
	{
		m_mainHole[0]->update();
	}
	
	clearLogData(1);
}

void Correlator::initSplice( void )
{
	// delete m_splicerholes
	vector<Hole*>::iterator iter;
	Hole* tempHole = NULL;
	for(iter = m_splicerholes.begin(); iter != m_splicerholes.end(); iter++) 
	{
		tempHole = (Hole*) *iter;
		if(tempHole) 
		{
			delete tempHole;
			tempHole = NULL;
		}
	}
	m_splicerholes.clear();	
	m_tiepoint = NULL;
	m_mainHole[0] = NULL;
	m_mainHole[1] = NULL;
	m_sagan_corename = "";	
		
	Core* coreptr = NULL;
	Value* valueptr = NULL;
	Tie* tieptr = NULL;
	int tie_id;
	for(int i = 0; i <= m_spliceOrder; i++)
	{
		tieptr = findTie(i);
		if(tieptr)
		{
			tie_id = tieptr->getId();
			coreptr = tieptr->getTieTo();
			if(coreptr)
			{
				valueptr = tieptr->getTieToValue();
				if(valueptr && valueptr->getValueType() == INTERPOLATED_VALUE)
				{
					coreptr->deleteInterpolatedValue(valueptr->getNumber());
				}
				coreptr->deleteTie(tie_id);
			}
								
			coreptr = tieptr->getTied();
			if(coreptr)
			{
				valueptr = tieptr->getTiedValue();
				if(valueptr && valueptr->getValueType() == INTERPOLATED_VALUE)
				{
					coreptr->deleteInterpolatedValue(valueptr->getNumber());
				}
				coreptr->deleteTie(tie_id);	
			}
			delete tieptr;
			tieptr = NULL;	
		}
	}
	m_spliceOrder = 0;
	m_ties.clear();		
	m_splicerties.clear();	
	
}

void Correlator::clearLogData( int flag )
{
	// clear all ties
	if(flag == 0)
	{
		//std::cout << "[Debug] clear all log... " << std::endl;
		Tie* tieptr = NULL;
		TieInfo* infoTieTo = NULL;
		TieInfo* infoTied = NULL;	
		int index =0;
		std::vector<Tie*>::iterator iter;
		Core* coreptr;
		Value* valueptr;
		Hole* holeptr;
		int numCores, numTies;
	
		int numHoles = m_dataptr->getNumOfHoles();	
		for(int i=0; i < numHoles; i++)
		{
			holeptr = m_dataptr->getHole(i);
			if(holeptr == NULL) continue;
			numCores =  holeptr->getNumOfCores();		
			for(int j=0; j <= numCores; j++)
			{
				coreptr = holeptr->getCore(j);
				if(coreptr == NULL) continue;
				numTies = coreptr->getNumOfTies(SAGAN_TIE);
				for(int k=0; k <= numTies; k++)
				{
					tieptr = coreptr->getTie(SAGAN_TIE, k);
					if(tieptr == NULL) continue;

					infoTieTo = tieptr->getInfoTieTo();
					infoTied = tieptr->getInfoTied();				
					
					index = tieptr->getId();
					coreptr = infoTied->m_coreptr;
					if(coreptr)
					{	
						valueptr = tieptr->getTiedValue();
						if(valueptr && valueptr->getValueType() == INTERPOLATED_VALUE)
						{
							coreptr->deleteInterpolatedValue(valueptr->getNumber());
						}
						infoTied->m_coreptr->deleteTie(index);
					}
					coreptr = infoTieTo->m_coreptr;
					if(coreptr)
					{	
						valueptr = tieptr->getTieToValue();
						if(valueptr && valueptr->getValueType() == INTERPOLATED_VALUE)
						{
							coreptr->deleteInterpolatedValue(valueptr->getNumber());
						}	
					
						infoTied->m_coreptr->deleteTie(index);
					}
					numTies --;
					k --;
					delete 	tieptr;
					tieptr = NULL;	
				}		
				numTies = coreptr->getNumOfTies(SAGAN_FIXED_TIE);
				for(int k=0; k <= numTies; k++)
				{
					tieptr = coreptr->getTie(SAGAN_FIXED_TIE, k);
					if(tieptr == NULL) continue;

					infoTieTo = tieptr->getInfoTieTo();
					infoTied = tieptr->getInfoTied();				
					
					index = tieptr->getId();
					coreptr = infoTied->m_coreptr;
					if(coreptr)
					{	
						valueptr = tieptr->getTiedValue();
						if(valueptr && valueptr->getValueType() == INTERPOLATED_VALUE)
						{
							coreptr->deleteInterpolatedValue(valueptr->getNumber());
						}
						infoTied->m_coreptr->deleteTie(index);
					}
					coreptr = infoTieTo->m_coreptr;
					if(coreptr)
					{	
						valueptr = tieptr->getTieToValue();
						if(valueptr && valueptr->getValueType() == INTERPOLATED_VALUE)
						{
							coreptr->deleteInterpolatedValue(valueptr->getNumber());
						}	
					
						infoTied->m_coreptr->deleteTie(index);
					}
					numTies --;
					k --;
					delete 	tieptr;
					tieptr = NULL;	
				}			
			}	
		}	

	}
	
	m_sagantotalties.clear();
	m_saganties.clear();

	if(m_logdataptr)
	{
		m_logdataptr->init();
	}
}

void Correlator::clearStratData( void )
{
	if(m_dataptr == NULL) return;
	
	int numHoles = m_dataptr->getNumOfHoles();
    int numCores;

	Hole* holeptr;
	Core* coreptr;
	for(int i=0; i < numHoles; i++)
	{
			holeptr = m_dataptr->getHole(i);
			if(holeptr == NULL) continue;
			numCores =  holeptr->getNumOfCores();
            for(int j=0; j < numCores; j++)
			{
					coreptr = holeptr->getCore(j);
					if(coreptr == NULL) continue;
					coreptr->deleteStrat();
        	}
	}

}

void Correlator::applyFilter( Actor* filter )
{
	if(m_mainHole[0] != NULL)
	{
		m_mainHole[0]->init(QUALITY_SPLICE);
		m_mainHole[0]->accept(filter);
		m_mainHole[0]->update();
	}
	if(m_mainHole[1] != NULL)
	{
		m_mainHole[1]->init(QUALITY_SPLICE);
		m_mainHole[1]->accept(filter);
		m_mainHole[1]->update();
	}	
}
	

void Correlator::resetELD( void )
{
	if(m_dataptr == NULL) return;
	
	int numHoles = m_dataptr->getNumOfHoles();
    int numCores, numValues;

	Hole* holeptr;
	Core* coreptr;
	Value* valueptr = NULL;
	for(int i=0; i < numHoles; i++)
	{
		holeptr = m_dataptr->getHole(i);
		if(holeptr == NULL) continue;
		numCores =  holeptr->getNumOfCores();
		for(int j=0; j < numCores; j++)
		{
			coreptr = holeptr->getCore(j);
			if(coreptr == NULL) continue;
			for(int k=0; k < numValues; k++)
			{
				valueptr = coreptr->getValue(k);
				if(valueptr == NULL) continue;
				valueptr->resetELD();
				//cout << "inside " << coreptr->getName() << coreptr->getNumber() << " " << i << endl;
			}


		}
	}
	m_dataptr->update();

}

Value*	Correlator::getTiePoint( void )
{
	return m_tiepoint;
}
	
int Correlator::setCoreQuality( char* hole, int core, int coretype, int quality, char* annot )
{
	Core* coreptr = findCore(coretype, hole, core, annot);
	if(coreptr == NULL) return 0;
	
	coreptr->setQuality(quality);
	//cout << "quality " << quality << " " << hole << " " << core << endl;
	
	return 1;
}

void Correlator::assignData( Data* dataptr )
{
	m_dataptr = dataptr;
	if(m_dataptr)	
	{
		m_correlatorData.setSite((char*)m_dataptr->getSite());
		m_correlatorData.setLeg((char*)m_dataptr->getLeg());
	}
}

int Correlator::undo(void)
{
	char* holeA;
	int nholeA;
	int coreidA;
	Core* coreptrA = NULL;
	
	if(m_givenCore != NULL)
	{	
		holeA = (char*) m_givenCore->getName();
		coreidA = m_givenCore->getNumber();
		nholeA = m_dataptr->getNumOfHoles(holeA);
		m_givenCore->undo();	
#ifdef DEBUG
		cout << "[Composite] Undo " << endl;
#endif	
		/*for(int i =1; i < nholeA; i++)
		{
			coreptrA = findCore(holeA, coreidA, i);
			if(coreptrA == NULL) continue;
			coreptrA->undo();
		}*/
		
		//m_dataptr->update();
		//m_dataptr->update();
		coreptrA = m_givenCore;		
		m_givenCore = NULL;
		//return 1;		
	} else {
		Tie* tieptr = NULL;
		std::vector<Tie*>::iterator iter;
		for(iter = m_ties.begin(); iter != m_ties.end(); iter++)
		{
			tieptr = (Tie*) *iter;
		}
		if(tieptr == NULL) return -1;
		//m_ties.erase(iter);

		//tieptr->setApply(NO);
		coreptrA = tieptr->getTieTo();
		tieptr->disable();
		if (coreptrA == NULL) 
			return 0;
			
		coreptrA->undo();
	}
	
	Hole* holeptrA = (Hole*) coreptrA->getParent();
	
	holeA = (char*) coreptrA->getName();
	coreidA = coreptrA->getNumber();
	int coretype = holeptrA->getType();
	const char* annot = NULL;
	if (coretype == USERDEFINEDTYPE)
		annot = holeptrA->getAnnotation();
		
	// HYEJUNG
	/*nholeA = m_dataptr->getNumOfHoles(holeA);	
	for(int i =1; i < nholeA; i++)
	{
		coreptrA = findCore(holeA, coreidA, i);
		if(coreptrA == NULL) continue;
		coreptrA->undo();
	}*/
	int numHoles = m_dataptr->getNumOfHoles();
	int numCores;
	Hole* holeptr;
	Core* coreptr = NULL;
	for(int i=0; i < numHoles; i++)
	{
		holeptr = m_dataptr->getHole(i);
		if(holeptr == NULL) continue;
		if(strcmp((char*)holeptr->getName(), holeA) == 0)
		{
			if (coretype == USERDEFINEDTYPE) 
			{
				if (strcmp(holeptr->getAnnotation(), annot) == 0)
					continue;
			} else if(holeptr->getType() == coretype)
				continue;
						
			numCores =  holeptr->getNumOfCores();
			for(int j=0; j <= numCores; j++)
			{
				coreptr = holeptr->getCore(j);
				if(coreptr == NULL) continue;
				if(coreptr->getNumber() == coreidA)
				{	
					coreptr->undo();	
					break;		
				}
			}
		}
	}		
	
	
	

	if(m_belowflag ==true)
	{
		m_belowflag = false;
 		//coreptrA = tieptr->getTieTo();

		int numHoles = m_dataptr->getNumOfHoles();
        	int numCores;

        	Hole* holeptr;
        	Core* coreptr;
        	Value* value = NULL;
        	for(int i=0; i < numHoles; i++)
        	{
                	holeptr = m_dataptr->getHole(i);
                	if(strcmp((char*)holeptr->getName(), (char*)coreptrA->getName()) == 0)
                	{
                        	numCores =  holeptr->getNumOfCores();
                        	for(int j=0; j < numCores; j++)
                        	{
                                	coreptr = holeptr->getCore(j);
                                	if(coreptr == NULL) continue;
                                	if(coreptr->getNumber() > coreptrA->getNumber())
                                	{
                                       		//value = coreptr->getValue(0);
                                        	//coreptr->setDepthOffset(0, value->getType(), true);
                                        	coreptr->undo();
                                	}
                        	}
                	}
        	}

	}

#ifdef DEBUG
                cout << "[Composite] Undo " << endl;
#endif

	m_dataptr->update();
	m_dataptr->update();
	return 1;

}

int Correlator::undoAbove(char* hole, int coreid)
{
	if(m_dataptr == NULL) return -1;

	//cout << "undo above ----------- " << hole << " " << coreid << endl;
	
	int numHoles = m_dataptr->getNumOfHoles();
	int numCores;

	Hole* holeptr;
	Core* coreptr;
	Value* value = NULL;
	char* hole_ptr;
	for(int i=0; i < numHoles; i++)
	{
			holeptr = m_dataptr->getHole(i);
			hole_ptr = (char*) holeptr->getName();
			if(strcmp(hole_ptr, hole) == 0)
			{
					numCores =  holeptr->getNumOfCores();
					for(int j=0; j < numCores; j++)
					{
							coreptr = holeptr->getCore(j);
							if(coreptr == NULL) continue;
							if(coreptr->getNumber() < coreid)
							{
									//cout << "undo -- " << coreptr->getNumber() << endl;
									value = coreptr->getValue(0);
									coreptr->disableTies();
									coreptr->setDepthOffset(0, value->getType(), true);
							}
					}
			}
	}


#ifdef DEBUG
	cout << "[Composite] Undo Above " << hole << coreid << endl;
#endif
	m_dataptr->update();
	m_dataptr->update();

	return 1;

}

double Correlator::getDataAtDepth( char* hole, int coreid, double depth, int coretype, char* annot )
{
	Core* coreptr = findCore(coretype, hole, coreid, annot);
	if(coreptr == NULL) return -999;
	Value* valueptr = findValue(coreptr, depth);
	if (valueptr == NULL) return -999;
	
	return valueptr->getData();
}


// relativepos --> 0 to 1
/*int Correlator::composite(int coreidA, double relativeposA, int coreidB, double relativeposB)
{
	Tie* tieptr = createTie(COMPOSITED_TIE, coreidA, relativeposA, coreidB, relativeposB);
	if(tieptr == NULL)
		return -1;

	return 1;
}*/

void  Correlator::setFloating( bool flag )
{
	m_floating = flag;
}
 
 
double Correlator::compositeBelow(char* holeA, int coreidA, double posA, char* holeB, int coreidB, double posB, int coretype, char* annot)
{
	//int nholeA = m_dataptr->getNumOfHoles(holeA);
	//cout << " nholeA = " << nholeA << endl;	
	Core* coreptrA = findCore(coretype, holeA, coreidA, annot);
	if(coreptrA == NULL) return 0;

	Core* coreptrB = NULL;
	coreptrB = findCore(coretype, holeB, coreidB, annot);
	if(coreptrB == NULL) return 0;

	Tie* tieptr  = createTie(COMPOSITED_TIE, coreptrA, posA, coreptrB, posB);
	if(tieptr == NULL) return -1;
	double offset = posB - posA;
	//cout << "offset = " << offset << ", ";
	
	Value* value = NULL;
	/*for(int i=1; i < nholeA; i++)
	{
		//coreptrA = findCore(coretype, holeA, coreidA, annot, i);
		coreptrA = findCore(holeA, coreidA, i);
		if(coreptrA == NULL) continue;
		value = coreptrA->getValue(0);
		if(value == NULL) continue;
		coreptrA->setOffsetByAboveTie(offset, value->getType());		
	}*/		

	m_dataptr->update();

	//double offset = posB - posA;
	//offset = tieptr->getOffset();
	//cout << offset << endl;
	//std::cout << "-------> offset : " << offset << std::endl;

	int numHoles = m_dataptr->getNumOfHoles();
	int numCores;

	Hole* holeptr;
	Core* coreptr;
	bool diff_type_flag = false;
	char* hole_ptr;
	for(int i=0; i < numHoles; i++)
	{
		holeptr = m_dataptr->getHole(i);
		if(holeptr == NULL) continue;
		hole_ptr = (char*) holeptr->getName();
		//cout << "holename = " << hole_ptr << " " << holeA << endl;
		if(strcmp(hole_ptr, holeA) == 0)
		{
			diff_type_flag = false;
			if(holeptr->getType() != coretype)
			{
				diff_type_flag = true;
			} else if (coretype == USERDEFINEDTYPE) 
			{
				if (strcmp(holeptr->getAnnotation(), annot) != 0)
					diff_type_flag = true;
			}				
			numCores =  holeptr->getNumOfCores();
			for(int j=0; j <= numCores; j++)
			{
				coreptr = holeptr->getCore(j);
				if(coreptr == NULL) continue;


				//if(coreptr->getNumOfTies(COMPOSITED_TIE) > 0)
				//	cout << coreptr->getNumOfTies(COMPOSITED_TIE)  << endl;
				
				if(coreptr->getNumber() > coreidA)
				{
					value = coreptr->getValue(0);
					if(value == NULL) 
					{
						coreptr->setOffsetByAboveTie(offset, 'X');
						continue;
					}
					coreptr->disableTies();
					//coreptr->setDepthOffset(offset, value->getType(), true);
					coreptr->setOffsetByAboveTie(offset, value->getType());
				}
				if((diff_type_flag == true) && (coreptr->getNumber() == coreidA))
				{
					value = coreptr->getValue(0);
					if(value == NULL) 
					{
						coreptr->setOffsetByAboveTie(offset, 'X');
						continue;
					}
					coreptr->disableTies();
					//coreptr->setDepthOffset(offset, value->getType(), true);
					coreptr->setOffsetByAboveTie(offset, value->getType());	
				}
			}
		}
	}

	m_belowflag = true;

	m_dataptr->update();
	m_dataptr->update();

#ifdef DEBUG
	cout << "[Composite Below] " << endl;
#endif
	m_givenCore = NULL;

	//double coef = tieptr->getCoef();
	//return coef;
	return 1.0f;
}


int Correlator::composite(char* holeA, int coreidA, double offset, int coretype, char* annot)
{
	//int nholeA = m_dataptr->getNumOfHoles(holeA);
	//cout << " core type = " << coretype << endl;
	//cout << "------------------------" << endl;
    Core* coreptr = findCore(coretype, holeA, coreidA, annot);
    if(coreptr == NULL) 
	{
#ifdef DEBUG
        cout << "[Composite] Error : can not find core" << endl;
#endif
		return -1;
	}
	Value* value = coreptr->getValue(0);
	coreptr->setOffsetByAboveTie(offset, value->getType());
	m_givenCore = coreptr;

	int numHoles = m_dataptr->getNumOfHoles();
	int numCores;
	Hole* holeptr;
	char* hole_ptr;
	for(int i=0; i < numHoles; i++)
	{
		holeptr = m_dataptr->getHole(i);
		if(holeptr == NULL) continue;
		hole_ptr = (char*) holeptr->getName();
		if(strcmp(hole_ptr, holeA) == 0)
		{
			if (coretype == USERDEFINEDTYPE) 
			{
				if (strcmp(holeptr->getAnnotation(), annot) == 0)
					continue;
			} else if(holeptr->getType() == coretype)
				continue;
						
			numCores =  holeptr->getNumOfCores();
			for(int j=0; j <= numCores; j++)
			{
				coreptr = holeptr->getCore(j);
				if(coreptr == NULL) continue;
				if(coreptr->getNumber() == coreidA)
				{	
					value = coreptr->getValue(0);
					if(value == NULL) continue;
					//coreptr->setDepthOffset(offset, value->getType(), true);
					coreptr->setOffsetByAboveTie(offset, value->getType());	
					break;		
				}
			}
		}
	}
		
	m_dataptr->update();
	m_dataptr->update();	
	return 1.0f;
}

int Correlator::compositeBelow(char* holeA, int coreidA, double offset, int coretype, char* annot)
{
    Core* coreptr = findCore(coretype, holeA, coreidA, annot);
    if(coreptr == NULL) 
	{
#ifdef DEBUG
        cout << "[Composite] Error : can not find core" << endl;
#endif
		return -1;
	}
	Value* value = coreptr->getValue(0);
	coreptr->setOffsetByAboveTie(offset, value->getType());
	m_givenCore = coreptr;
	
	
	int numHoles = m_dataptr->getNumOfHoles();
	int numCores;
	Hole* holeptr;

	bool diff_type_flag = false;
	char* hole_ptr;
	for(int i=0; i < numHoles; i++)
	{
		holeptr = m_dataptr->getHole(i);
		if(holeptr == NULL) continue;
		hole_ptr = (char*) holeptr->getName();
		if(strcmp(hole_ptr, holeA) ==0)
		{
			diff_type_flag = false;
			if(holeptr->getType() != coretype)
			{
				diff_type_flag = true;
			} else if (coretype == USERDEFINEDTYPE) 
			{
				if (strcmp(holeptr->getAnnotation(), annot) != 0)
					diff_type_flag = true;
			}				
			numCores =  holeptr->getNumOfCores();
			for(int j=0; j <= numCores; j++)
			{
				coreptr = holeptr->getCore(j);
				if(coreptr == NULL) continue;
				if(coreptr->getNumber() > coreidA)
				{
					value = coreptr->getValue(0);
					if(value == NULL) continue;
					//coreptr->setDepthOffset(offset, value->getType(), true);
					coreptr->setOffsetByAboveTie(offset, value->getType());
				}
				if((diff_type_flag == true) && (coreptr->getNumber() == coreidA))
				{
					value = coreptr->getValue(0);
					if(value == NULL) continue;
					//coreptr->setDepthOffset(offset, value->getType(), true);
					coreptr->setOffsetByAboveTie(offset, value->getType());				
				}
			}
		}
	}

	m_belowflag = true;
			
	m_dataptr->update();
	m_dataptr->update();	
	return 1.0f;
}

double Correlator::composite(char* holeA, int coreidA, double posA, char* holeB, int coreidB, double posB, int coretype, char* annot)
{
	Core* coreptrA = findCore(coretype, holeA, coreidA, annot);
	Core* coreptrB = findCore(coretype, holeB, coreidB, annot);
		
    if(coreptrA == NULL || coreptrB == NULL) 
	{
#ifdef DEBUG
        cout << "[Composite] Error : can not find core" << endl;
#endif
		return -1;
	}

	Tie* tieptr = createTie(COMPOSITED_TIE, coreptrA, posA, coreptrB, posB);
	if(tieptr == NULL) return -1;
	Value* value = NULL;
	double offset = posB - posA;
	
	m_dataptr->update();
	offset = tieptr->getOffset();
	
	int numHoles = m_dataptr->getNumOfHoles();
	int numCores;
	Hole* holeptr;
	Core* coreptr;
	char* hole_ptr;
	
	for(int i=0; i < numHoles; i++)
	{
		holeptr = m_dataptr->getHole(i);
		if(holeptr == NULL) continue;
		hole_ptr = (char*) holeptr->getName();
		
		if(strcmp(hole_ptr, holeA) == 0)
		{
			if (coretype == USERDEFINEDTYPE) 
			{
				if (strcmp(holeptr->getAnnotation(), annot) == 0)
					continue;
			} else if(holeptr->getType() == coretype)
				continue;
				
			numCores =  holeptr->getNumOfCores();
			for(int j=0; j <= numCores; j++)
			{
				coreptr = holeptr->getCore(j);
				if(coreptr == NULL) continue;
				if(coreptr->getNumber() == coreidA)
				{	
					value = coreptr->getValue(0);
					if(value == NULL) continue;
					coreptr->disableTies();
					coreptr->setDepthOffset(offset, value->getType(), true);
					//cout << "got here ---------------- " << coreptr->getName() << coreptr->getNumber() << " "  << offset << " " << holeptr->getType() << endl;
					//coreptr->setOffsetByAboveTie(offset, value->getType());	
					break;		
				}
			}
		}
	}
		
	m_dataptr->update();
	m_dataptr->update();
	m_givenCore = NULL;
	return 1.0f;
}

double Correlator::getRate(double depth)
{
	if(m_mainHole[0] == NULL) return 1.0;
	
	Value* valueA = findValueInHole( m_mainHole[0], depth );
	if (valueA == NULL) return 1.0;
	
	double rate = valueA->getMcd() / valueA->getMbsf();
	
	return rate;
}

	
int Correlator::splice(char* hole, int coreid, int type, char* annot, bool append)
{
	if(m_dataptr == NULL) return -1;

	m_tiepoint = NULL;
	Core* source = findCore(type, hole, coreid, annot);
	if(source == NULL)
	{
#ifdef DEBUG
		cout << "[Splice] Error : can not find core" << endl;
#endif
		return -1;
	}
	int ret;	
	ret = splice(source, append);	
	updateSaganTies();
	return ret;
}

int Correlator::splice(Core* source, bool append)
{
	if(m_dataptr == NULL) return -1;
	if(source == NULL) return -1;

	Core* coreptr = NULL;
	if(append == false)
	{
		if(m_mainHole[0] != NULL) 
		{
			delete m_mainHole[0];
			m_mainHole[0] = NULL;
			m_splicerholes.clear();

		} 
		createSpliceHole();

		coreptr = m_mainHole[0]->createCore(0);
	} else 
	{
		int no = m_mainHole[0]->getNumOfCores();
		coreptr = m_mainHole[0]->createCore(no);
	}
	if(coreptr == NULL) return -1;	
	
	coreptr->copy(source);
	char annotation[25];
	memset(annotation, 0, 25);
	sprintf(annotation, "%s%d", source->getName(), source->getNumber());
	coreptr->setAnnotation(&annotation[0]);	
	
    int coretype = source->getType();
    coreptr->setType(coretype);

    int index = 0;
    int size = source->getNumOfValues();
    Value* newValue = NULL;
    for(int i=0 ; i < size; i++, index++)
    {
			newValue = coreptr->createValue(index);
			if(source->getQuality() != GOOD)  continue;
            newValue->copy(source->getValue(i));
	}
		
	m_mainHole[0]->update();
	m_mainHole[0]->update();	
	
#ifdef DEBUG
	cout << "[Splice] ";
	cout << source->getSite() << " " << source->getLeg() << " " << source->getName() << " " << source->getNumber() << " " << source->getRange()->mindepth << " " << source->getRange()->maxdepth << endl;
#endif	
	return 1;
}

//int Correlator::splice(int id, char holeA, int coreidA, double posA, char holeB, int coreidB, double posB, int type, bool append)
int Correlator::splice(int tie_id, int typeA, char* annotA, char* holeA, int coreidA, double posA, int typeB, char* annotB, char* holeB, int coreidB, double posB, bool append)
{
	if(m_dataptr == NULL) return -1;
	m_tiepoint = NULL;
	//cout << "type = " << typeA << " " << typeB << endl;
	
	if(m_spliceOrder == 0) 
	{
		if(m_mainHole[0]) 
		{
			delete m_mainHole[0];
			m_mainHole[0] = NULL;
			m_splicerholes.clear();
			createSpliceHole();
		}
	}
	
	Core* coreptrA = findCore(typeA, holeA, coreidA, annotA);
	Core* coreptrB = findCore(typeB, holeB, coreidB, annotB);
	//cout << "splice - > " << typeA << " " << typeB << endl;

	if(coreptrA == NULL || coreptrB == NULL)
	{
#ifdef DEBUG
			cout << "[Splice] Error : can not find core" << endl;
#endif
			return  -1;
	}

	int ret =0;
	ret = splice(tie_id, coreptrA, coreptrB, posA, posB, append);

	m_mainHole[0]->update();
	m_mainHole[0]->update();
	m_dataptr->update();
	return ret;
}

int Correlator::splice(int coreidA, double relativeposA, int coreidB, double relativeposB)
{
	if(m_dataptr == NULL) return -1;

	if(m_mainHole[0] == NULL) 
	{
		createSpliceHole();
	}

	// find coreA and coreB
	Core* coreA = findCoreinSplice(coreidA);
	if(coreA == NULL) 
	{
		coreA = findCore(coreidA);
	}
	Core* coreB = findCore(coreidB);	// coreto
	if(coreA == NULL || coreB == NULL) return -1;

	double posA = (coreA->getBottom() - coreA->getTop()) * relativeposA;
	double posB = (coreB->getBottom() - coreB->getTop()) * relativeposB;

	//splice(coreA, coreB, posA, posB);

	return 1;
}


int Correlator::splice(void)
{
	if(m_mainHole[0] != NULL) 
	{
		Core* core_temp_ptr = m_mainHole[0]->getCore(0);
		if(core_temp_ptr != NULL)
		{
			Core* core_ptr = findCore(core_temp_ptr->getType(), core_temp_ptr->getName(), core_temp_ptr->getNumber(), core_temp_ptr->getAnnotation());
			if(core_ptr != NULL)
			{
				int value_index = core_ptr->getNumOfValues()-1;
				Value* value_ptr = core_ptr->getValue(value_index);
				if(value_ptr != NULL)
					return splice(-1, core_ptr, core_ptr, value_ptr->getELD(), value_ptr->getELD(), false, true);
			}

		}
	}
	
	return 1;
}


int Correlator::splice(int tie_id, Core* coreA, Core* coreB, double posA, double posB, bool append, bool appendbegin)
{
	int type = REAL_TIE;
	//if(appendbegin == true)
	//	type = DUMMY_TIE;

	data_range rangeA, rangeB;
	rangeA.top = posA;
	rangeA.bottom = rangeA.top;
	rangeB.top = posB;
	rangeB.bottom = rangeB.top;

	//cout << coreA->getName() << coreA->getNumber() << " " << coreB->getName() << coreB->getNumber() << endl;
	//cout << "------------------- " <<  coreA->getName() << coreA->getNumber() << " " << posA << " : " << coreB->getName() << coreB->getNumber() << " " << posB << endl;
	
	
	// find value.....
	Value* valueA = findValue(coreA, rangeA.top);

	double depth;
	Value* newValue = NULL;
	Value* temp_newValue  = NULL;
	double temp_data;
	double temp_top;
	int idx;
	if(valueA && valueA->getMcd() != rangeA.top)
	{
		//std::cout << "--> A - > " << valueA->getMcd() << " "<< rangeA.top << std::endl;

		depth = rangeA.top- coreA->getDepthOffset();
		double offset = posB- posA;
		idx = valueA->getNumber();
		temp_data = valueA->getRawData();
		if(depth <  valueA->getMbsf())
		{
			temp_newValue = coreA->getValue(idx-1);
			if(temp_newValue)
			{
				temp_data= getData(temp_newValue, valueA, rangeA.top); 
				temp_top =temp_newValue->getTop() + (rangeA.top - temp_newValue->getMcd()) * 100;
				//temp_top= getTop(temp_newValue, valueA, rangeA.top);
			}
			//std::cout << "--> smaller " << temp_newValue->getRawData() << " " << valueA->getRawData() << " " << temp_data << std::endl; 
			//std::cout << "--> smaller " << temp_newValue->getTop() << " " << valueA->getTop() << " " << temp_top << std::endl; 
		} else 
		{
			temp_newValue = coreA->getValue(idx+1);
			if(temp_newValue)
			{
				temp_data = getData(valueA, temp_newValue, rangeA.top); 
				temp_top =valueA->getTop() + (rangeA.top - valueA->getMcd()) * 100;
 				//temp_top= getTop(valueA, temp_newValue, rangeA.top); 				

			}			
			//std::cout << "--> bigger " << valueA->getRawData()  << " " << temp_newValue->getRawData() << " " << temp_data << std::endl;
			//std::cout << "--> bigger " << valueA->getTop() << " " << temp_newValue->getTop() << " " << temp_top << std::endl; 			
		}		
		//std::cout << "-------------- 2 " << std::endl;
		
		newValue = coreA->createInterpolatedValue(depth);
		if(newValue && (newValue->getMbsf() != depth))
		{
				newValue->copy(valueA);
				newValue->setValueType(INTERPOLATED_VALUE);
				
				newValue->setDepth(depth);
				newValue->applyAffine(coreA->getDepthOffset(), newValue->getType());
				newValue->setB(offset);
				// need to update data and bottom/top value
				newValue->setRawData(temp_data);
				newValue->setTop(temp_top);
				valueA = newValue;
				//std::cout << "--> new value is created.... "  << newValue->getTop() << " " << newValue->getMbsf() << ", " << newValue->getMcd() << " " << valueA->getNumber() << std::endl;
		}
	}
	
	Value* valueB = findValue(coreB, rangeB.top);
	if(valueB && valueB->getMcd() != rangeB.top)
	{
		//std::cout << "--> B - > " << valueB->getMcd() << " "<< rangeB.top << std::endl;	

		depth = rangeB.top- coreB->getDepthOffset();
		idx = valueB->getNumber();
		temp_data = valueB->getRawData();
		if(depth <  valueB->getMbsf())
		{
			temp_newValue = coreB->getValue(idx-1);
			if(temp_newValue)
			{
				temp_data= getData(temp_newValue, valueB, rangeB.top); 
				temp_top =temp_newValue->getTop() + (rangeB.top - temp_newValue->getMcd()) * 100;
				//temp_top= getTop(temp_newValue, valueB, rangeB.top);	
			}
			//std::cout << "--> smaller " << temp_newValue->getRawData() << " " << valueB->getRawData() << " " << temp_data << std::endl;
			//std::cout << "--> smaller " << temp_newValue->getTop() << " " << valueB->getTop() << " " << temp_top << std::endl; 				
		} else 
		{
			temp_newValue = coreB->getValue(idx+1);
			if(temp_newValue)
			{
				temp_data= getData(valueB, temp_newValue, rangeB.top); 
				temp_top =valueB->getTop() + (rangeB.top - valueB->getMcd()) * 100;
				//temp_top= getTop(valueB, temp_newValue, rangeB.top);
			}			
			//std::cout << "--> bigger " << valueB->getRawData()  << " " << temp_newValue->getRawData() << " " << temp_data << std::endl;
			//std::cout << "--> bigger " << valueB->getTop() << " " << temp_newValue->getTop() << " " << temp_top << std::endl; 			
		}		
		newValue = coreB->createInterpolatedValue(depth);
		if(newValue && (newValue->getMbsf() != depth))
		{
				newValue->copy(valueB);
				newValue->setValueType(INTERPOLATED_VALUE);
				
				newValue->setDepth(depth);
				newValue->applyAffine(coreB->getDepthOffset(), newValue->getType());
				// need to update data and bottom/top value				
				newValue->setRawData(temp_data);		
				newValue->setTop(temp_top);		
				valueB = newValue;
#ifdef DEBUG				
				std::cout << "[DEBUG] new value is created.... " << newValue->getTop() << " " <<  newValue->getMbsf() << ", " << newValue->getMcd() << " " << valueA->getNumber() << std::endl;
#endif
		}
	}
	
	if(valueA == NULL || valueB == NULL) 
        {
#ifdef DEBUG
                cout << "[Splice] Error : can not find value " << "(" << posA << " - " << posB << ")" << endl;
				// TEST
				if (valueA == NULL)
					cout << "[DEBUG] posA ..... error.. not found " << endl;
				if (valueB == NULL)
					cout << "[DEBUG] posB ..... error.. not found " << endl;
				
#endif
                return -1;
        }

	rangeA.top = valueA->getTop();
	rangeA.bottom = rangeA.top;
	rangeB.top = valueB->getTop();
	rangeB.bottom = rangeB.top;
	
	// create Tie and register.......
	Tie* tieptr = NULL;
	if (tie_id == -1) 
	{
		tieptr = new Tie(REAL_TIE);
		if(appendbegin == true)			
			tieptr->setDummy();
		
		tieptr->setOrder(m_spliceOrder);
		m_spliceOrder++;
		m_ties.push_back(tieptr);
	}
	else {
		Tie* tempTieptr;       
		std::vector<Tie*>::iterator iter;       
		for(iter = m_ties.begin(); iter != m_ties.end(); iter++) 
		{
			tempTieptr = (Tie*) *iter;
			if(tempTieptr->getId() == tie_id) 
			{
				tieptr = tempTieptr;
				break;
			}
		}
		if(tieptr == NULL) return 0;
		//tieptr->getTieTo()->deleteInterpolatedValue();
		if(tieptr->getTiedValue()->getValueType() == INTERPOLATED_VALUE)
		{
			tieptr->getTied()->deleteInterpolatedValue(tieptr->getTiedValue()->getNumber());
		}
		if(tieptr->getTieToValue()->getValueType() == INTERPOLATED_VALUE)
		{
			tieptr->getTieTo()->deleteInterpolatedValue(tieptr->getTieToValue()->getNumber());
		}
		
		tieptr->getTied()->deleteTie(tieptr->getId());
		// HYEJUNG NEED TO ADD CLEANUP ----------------------
	}

	if(posA != posB)
	{
		tieptr->setConstrained(false);
	}
	
	tieptr->setAppend(append);
	// msfd, mcd
	tieptr->setTieTo(coreA, valueA->getType(), valueA->getSection(), rangeA, valueA->getMbsf(), posA);
	tieptr->setTied(coreB, valueB->getType(), valueB->getSection(), rangeB, valueB->getMbsf(), posB);
	m_tiepoint =  valueA;
			
	valueA  = tieptr->getTiedValue();
	valueB  = tieptr->getTieToValue();

#ifdef DEBUG	
	std::cout << "[DEBUG] ---------P/a) " << valueA->getMbsf() << " " << valueA->getMcd() << " " << valueA->getNumber() << std::endl;		
	std::cout << "[DEBUG] --------P/b) " << valueB->getMbsf() << " " << valueB->getMcd() << " " << valueB->getNumber() << std::endl;	
#endif		
	coreB->addTie(tieptr);
	//std::cout << coreB << " " << coreB->getName() << coreB->getNumber() << " " << coreB->getType() << " " << coreB->getNumOfTies()  << std::endl;

#ifdef DEBUG
	cout << "[Splice] ";
	cout << coreA->getSite() << " " << coreA->getLeg() << " " << coreA->getName() << " " << coreA->getNumber() << " " << valueA->getType() << " " << valueA->getSection() << " " << valueA->getTop()  << " " << valueA->getBottom()  << " depth" << " tie to ";
	cout << coreB->getSite() << " " << coreB->getLeg() << " " << coreB->getName() << " " << coreB->getNumber() << " " << valueB->getType() << " " << valueB->getSection() << " " << valueB->getTop()  << " " << valueB->getBottom()  << " depth" << endl;
	if(appendbegin == true)
		cout << "\tAdditional Info: Dummy tie" << endl;
#endif	

	update();

	return tieptr->getId();

}

int Correlator::splice(int tieindex, int coreidA, double relativeposA, int coreidB, double relativeposB)
{
	if(m_dataptr == NULL) return -1;

	Tie* tieptr = NULL;
	Tie* tempTieptr;
	std::vector<Tie*>::iterator iter;
	for(iter = m_ties.begin(); iter != m_ties.end(); iter++)
	{
		tempTieptr = (Tie*) *iter;
		if(tempTieptr->getId() == tieindex)
		{
			tieptr = tempTieptr;
			break;
		}
	}
	if(tieptr == NULL) return 0;
	
	// find coreA and coreB
	Core* coreA = findCoreinSplice(coreidA);
	if(coreA == NULL) 
	{
		coreA = findCore(coreidA);
	}	
	Core* coreB = findCore(coreidB);	// coreto
	if(coreA == NULL || coreB == NULL) 
        {
#ifdef DEBUG
                cout << "[Splice] Error : can not find core" << endl;
#endif
                return -1;
        }
	
	// calculate all inforamtion : top/bottom...
	// top, bottom
	data_range rangeA, rangeB;
	rangeA.top = (coreA->getBottom() - coreA->getTop()) * relativeposA;
	rangeA.bottom = rangeA.top;
	rangeB.top = (coreB->getBottom() - coreB->getTop()) * relativeposB;
	rangeB.bottom = rangeB.top;
	
	// find value.....
	Value* valueA = findValue(coreA, rangeA.top);
	Value* valueB = findValue(coreB, rangeB.top);

	if(valueA == NULL || valueB == NULL)
        {
#ifdef DEBUG
                cout << "[Splice] Error : can not find value" << endl;
#endif
                return -1;
        }
		
	// create Tie and register.......
	if(tieptr->getTieTo()->getId() == valueB->getId()) 
	{
		tieptr->setTied(coreA, valueA->getType(), valueA->getSection(), rangeA);
		tieptr->setTieTo(coreB, valueB->getType(), valueB->getSection(), rangeB);
	} else 
	{
		tieptr->getTieTo()->deleteTie(tieptr->getId());
		tieptr->setTied(coreA, valueA->getType(), valueA->getSection(), rangeA);
		tieptr->setTieTo(coreB, valueB->getType(), valueB->getSection(), rangeB);
		coreB->addTie(tieptr);
	}

	// coreB --> above 
	int index = coreB->getNumber();
	Core* coreptr = m_mainHole[0]->getCoreByNo(index);
	if(coreptr == NULL) return -1;
	coreptr->reset();
	int coretype = coreB->getType();
 	coreptr->setType(coretype);	
	
	//assignAboveValues(coreptr, coreA, valueA);
	//assignBelowValues(coreptr, coreB, valueB);
	
	
#ifdef DEBUG
	cout << "[Splice] " << endl;
	cout << coreA->getSite() << " " << coreA->getLeg() << " " << coreA->getName() << " " << coreA->getNumber() << " " << valueA->getType() << " " << valueA->getSection() << " " << rangeA.top  << " " << rangeA.bottom  << " depth" << " tie to ";
	cout << coreB->getSite() << " " << coreB->getLeg() << " " << coreB->getName() << " " << coreB->getNumber() << " " << valueB->getType() << " " << valueB->getSection() << " " << rangeB.top  << " " << rangeB.bottom  << " depth" << endl;
#endif	

	update();

	return 1;
}

int Correlator::appendSplice( bool allflag )
{
	if(m_dataptr == NULL) return -1;
	
	Tie* tieptr = (Tie*) m_ties.back(); 
	if(tieptr == NULL) return 0;		
	Tie* tieptrNew = NULL;
		
	if(allflag == true)
	{
		if((tieptr->isAppend() == true) && tieptr->isAll() == false)
		{
			Core* coreA = tieptr->getTieTo();
			if (coreA == NULL) return -1;
			Hole* holeA = (Hole*) coreA->getParent();
			
			Hole* holeptr = m_dataptr->getHole((char*) coreA->getName(), holeA->getType(), (char*)holeA->getAnnotation());			
			if(holeptr != NULL)
			{
				int coreno = coreA->getNumber();
				coreno++;
				Core* coreptr= holeptr->getCoreByNo(coreno);
				if(coreptr)
				{			
					tieptrNew = new Tie(REAL_TIE);
					if(tieptrNew == NULL) return -1;
					tieptrNew->setOrder(m_spliceOrder);
					m_spliceOrder++;
					m_ties.push_back(tieptrNew);
					data_range range;
					range.top = 0.0f;
					tieptrNew->setAppend(true, true);

					tieptrNew->setTied(coreA, 'x', "0", range);	
					tieptrNew->setTieTo(coreptr, 'x', "0", range);	
					coreA->addTie(tieptrNew);	
				}
			}
		} else 
		{
			tieptr->setAppend(true, true);
		}
#ifdef DEBUG
	cout << "[Splice] append all cores below" << endl;
#endif
		
	} else 
	{
		Core* coreA = tieptr->getTieTo();
		if (coreA == NULL) return -1;
		Hole* holeA = (Hole*) coreA->getParent();
		
		Hole* holeptr = m_dataptr->getHole((char*) coreA->getName(), holeA->getType(), (char*) holeA->getAnnotation());
		if(holeptr != NULL)
		{
			int coreno = coreA->getNumber();
			coreno++;
			Core* coreptr= NULL;
			coreptr = holeptr->getCoreByNo(coreno);
			int holeno = holeptr->getNumOfCores();
			while(coreno < holeno)
			{ 
				if(coreptr)
				{
					if(coreptr->getNumOfValues() == 0)
					{
						coreno++;
						if(coreno == holeno) 
						{
							coreptr == NULL;
							break;
						}
						
					} else 
						break;
				}
			}
			if(coreno == holeno)
			{
#ifdef DEBUG			
				cout << "[Splice] ERROR : could not find append one core " << endl;			
#endif				
				coreptr = NULL;
			}

			if(coreptr)
			{
				tieptrNew = new Tie(REAL_TIE);
				if(tieptrNew == NULL) return -1;
				
				tieptrNew->setOrder(m_spliceOrder);
				m_spliceOrder++;
				m_ties.push_back(tieptrNew);
				data_range range;
				tieptrNew->setAppend(true, false);
				tieptrNew->setTied(coreA, 'x', "0", range);	
				tieptrNew->setTieTo(coreptr, 'x', "0", range);	
				coreA->addTie(tieptrNew);

#ifdef DEBUG
				//std::cout << coreA << " " << coreA->getName() << coreA->getNumber() << " " << holeA->getType() << " " << coreA->getNumOfTies() << std::endl;

				cout << "[Splice] append one core below : " << coreptr->getName() << coreptr->getNumber()  << endl;
#endif						
			}
		}
		
	}
	
	return 1;	
}


int Correlator::appendSelectedSplice(int type, char* annot, char* hole, int coreid)
{
	if(m_dataptr == NULL) return -1;
	
	Tie* tieptr = (Tie*) m_ties.back(); 
	if(tieptr == NULL) return 0;		
	Tie* tieptrNew = NULL;
		
	Core* coreA = tieptr->getTieTo();			// previous core
	if (coreA == NULL) return -1;
	Hole* holeA = (Hole*) coreA->getParent();  	// previous hole

	// next core
	Hole* holeptr = m_dataptr->getHole(hole, type, annot);

	if(holeptr != NULL)
	{
		Core* coreptr= NULL;
		coreptr = holeptr->getCoreByNo(coreid);
		if(coreptr)
		{
			if((strcmp(holeA->getName(), holeptr->getName()) == 0) && (coreA->getNumber() == coreptr->getNumber()))
				return 1;

			tieptrNew = new Tie(REAL_TIE);
			if(tieptrNew == NULL) return -1;
			
			tieptrNew->setOrder(m_spliceOrder);
			m_spliceOrder++;
			m_ties.push_back(tieptrNew);
			data_range range;
			tieptrNew->setAppend(true, false);
			tieptrNew->setTied(coreA, 'x', "0", range);	
			tieptrNew->setTieTo(coreptr, 'x', "0", range);	
			coreA->addTie(tieptrNew);
#ifdef DEBUG
			//std::cout << coreA << " " << coreA->getName() << coreA->getNumber() << " " << holeA->getType() << " " << coreA->getNumOfTies() << std::endl;

			cout << "[Splice] append one core below : " << coreptr->getName() << coreptr->getNumber()  << endl;
#endif						
		}
	}
		
	return 1;	
}

int Correlator::undoAppendSplice(void)
{
	if(m_dataptr == NULL) return -1;
	
	Tie* tieptr = (Tie*) m_ties.back(); 
	if(tieptr == NULL) return 0;	
	//tieptr->setAppend(false, false);

	TieInfo* info = tieptr->getInfoTieTo();
	//if((info->m_top == 0.0f) && (info->m_bottom <= -9999.0))

	if((tieptr->isAppend() == true) && (tieptr->isAll() == false))
	{
		int tieid = tieptr->getId();
		Core* coreptr = tieptr->getTied();

		if(coreptr != NULL) 
		{
			coreptr->deleteTie(tieid);
		}
		delete tieptr;
		tieptr = NULL;
		m_spliceOrder--;
		
		m_ties.pop_back();	
		
	} else {
		tieptr->setAppend(false, false);	
	}

#ifdef DEBUG
	cout << "[Splice] Undo All " << m_ties.size() << endl;
#endif	
	return 1;
}

void Correlator::deleteAllSplice(void)
{
	Tie* tieptr = NULL;       
	Core* coreptr = NULL;
	std::vector<Tie*>::iterator iter;
	for(iter = m_ties.begin(); iter != m_ties.end(); iter++)
	{
		tieptr = (Tie*) *iter; 
		if(tieptr == NULL) continue;
		if(tieptr->getType() == REAL_TIE)
		{
			m_ties.erase(iter);
        		coreptr = tieptr->getTied();
        		coreptr->deleteTie(tieptr->getId());
        		delete tieptr;
        		tieptr = NULL;
		}	
	}
	m_spliceOrder =0;
#ifdef DEBUG	
	cout << "[Splice] No splice Tie " << endl;
#endif
}

int Correlator::deleteSplice(int tieid)
{	
	Tie* tieptr = NULL;       
	
	if(tieid == 0)
	{
		tieptr = (Tie*) m_ties.back(); 
		if(tieptr == NULL) return 0;	
		tieid = tieptr->getId();	
	} else 
	{
		Tie* tempTieptr;       
		std::vector<Tie*>::iterator iter = m_ties.end();   
		
		int i =0;
		for(iter = m_ties.begin(); iter != m_ties.end(); iter++, i++)
		{
			tempTieptr = (Tie*) *iter; 
			if(tempTieptr == NULL) continue;

			if(tempTieptr->getId() == tieid)
			{
				tieptr = tempTieptr; 
				//m_ties.erase(iter);
				break;
			}
		}
	}
			
	if((tieptr->isAppend() == true) && (tieptr->isAll() == true))
	{
		tieptr->setAppend(false, false);
#ifdef DEBUG	
		cout << "[Splice] Undo All ";	
#endif
		return 1;	
	} 

	bool append= false;
	if((tieptr->isAppend() == true) && (tieptr->isAll() == false))
	{
		tieid = tieptr->getId();
#ifdef DEBUG		
		cout << "[Splice] Undo ";	
#endif
		append= true;
	}
	
	Core* coreptr = tieptr->getTied();
	if(coreptr != NULL) 
	{
#ifdef DEBUG	
		cout << coreptr->getName() << coreptr->getNumber() +1 << endl;	
#endif
		coreptr->deleteTie(tieid);
		//tieptr->getTieTo()->deleteInterpolatedValue();
		if(tieptr->getTiedValue())
			tieptr->getTied()->deleteInterpolatedValue(tieptr->getTiedValue()->getNumber());
		if(tieptr->getTieToValue())
			tieptr->getTieTo()->deleteInterpolatedValue(tieptr->getTieToValue()->getNumber());
	} /*else 
		cout << endl;	*/
	
	delete tieptr;
	tieptr = NULL;
	m_spliceOrder--;
	
	m_ties.pop_back();

	int ret = 0;
	if(m_spliceOrder <= 0) 
	{
		ret = splice(coreptr);
	}
	if(append == true) {
#ifdef DEBUG	
		cout << "[Splice] -append tie- Undo " << endl;	
#endif
		return 1;
	}
#ifdef DEBUG	
	cout << "[Splice] Undo " << endl;	
#endif
	return 1;
}

void  Correlator::generateSaganHole( void )
{
	if(m_mainHole[0] == NULL) {
#ifdef DEBUG	
		cout << "[generateSaganHole] ERROR : could not find main hole" << endl;
#endif
		return;
	}

	if(m_mainHole[1] != NULL) 
	{
		delete m_mainHole[1];
		m_mainHole[1] = NULL;
	} 

	m_mainHole[1] = new Hole(100, NULL);
	m_mainHole[1]->setName("X");
	m_mainHole[1]->setParent(&m_correlatorData);		
	m_mainHole[1]->copy(m_mainHole[0]);
	
	int numCore = m_mainHole[1]->getNumOfCores();
	//std::cout << "numCore - generateSagan : " << numCore << std::endl;
	int numValue;
	Core* coreptr;
	Value* valueptr;
	Value* sourceptr;
	for(int i=0; i <  numCore; i++)
	{
		coreptr = m_mainHole[1]->getCore(i);
		if(coreptr == NULL) continue;
		numValue = coreptr->getNumOfValues();
		for(int j=0; j < numValue; j++)
		{
			valueptr = coreptr->getValue(j);
			sourceptr = valueptr->getSource();
			if(sourceptr != NULL)
			{
				//std::cout <<coreptr->getName() << coreptr->getNumber() << " " << numValue << std::endl;
				if(sourceptr->getQuality() != GOOD)  continue;
				valueptr->copy(sourceptr);
			}
		}	
	}


}
	
void Correlator::generateSpliceHole(Hole* newSpliceHole) {
	if(m_dataptr == NULL) return;
	
	//cout << "[DEBUG] Generating Splice Hole is started" << endl;
	// how many real-tie
    int numHoles = m_dataptr->getNumOfHoles();
    int numCores, numTies;
	
	m_splicerties.clear();

    Hole* holeptr;
    Core* coreptr;
	Tie* tieptr;
	int count=0;
	
	for(int i=0; i < numHoles; i++)
	{
		holeptr = m_dataptr->getHole(i);
        if(holeptr == NULL) continue;
        numCores =  holeptr->getNumOfCores();
        for(int j=0; j <= numCores; j++)
        {
			coreptr = holeptr->getCore(j);
            if(coreptr == NULL) continue;
			numTies = coreptr->getNumOfTies();
			
            for(int k=0; k < numTies; k++)
			{
               	tieptr = coreptr->getTie(k);
				if(tieptr->getType() == REAL_TIE)
				{
					count++;
				}
            }
		}
	}
	
	//cout << "count =" << count << " " << m_ties.size() << endl;

	if (count == 0) return;
	m_spliceOrder = count;

	int order = 0;
    Core* coreA1 = NULL;
    Core* coreA2 = NULL;
    Core* coreB1 = NULL;
    Core* coreB2 = NULL;
    TieInfo* infoTieToA = NULL;
    TieInfo* infoTiedA = NULL;
    TieInfo* infoTieToB = NULL;
    TieInfo* infoTiedB = NULL;
	bool affinestatus = false;

	// create hole for splice
	if (newSpliceHole == NULL)
	{
		createSpliceHole();
		newSpliceHole = m_mainHole[0];
	}

	double offset=0;
	int noCore = 1;
	// first tie is for above : 
	tieptr = findTie(order);
	if(tieptr == NULL) 
	{
#ifdef DEBUG	
		cout << "[DEBUG]  NULL" << endl;
#endif
		return;
	}
	
	if(tieptr->isConstrained() == false)
		offset = tieptr->getOffset();

	m_splicerties.push_back(tieptr);
	
    coreA1 = tieptr->getTieTo();
    coreA2 = tieptr->getTied();
    infoTieToA = tieptr->getInfoTieTo();
	infoTiedA = tieptr->getInfoTied();


	// took data for above
	coreptr = newSpliceHole->createCore(noCore);
	//cout << "-----------------------> " << coreA2->getDepthOffset() << " " << coreA1->getDepthOffset() << endl;
	//double offset, bool applied = false, bool fromfile = false
	
	noCore++;
	int coretype = coreA1->getType();
	coreptr->setType(coretype);
	char annotation[25];
	memset(annotation, 0, 25);
	sprintf(annotation, "%s%d", coreA2->getName(), coreA2->getNumber());
	coreptr->setAnnotation(&annotation[0]);
	//cout << "1. annotation =" << coreA2->getName() <<  coreA2->getNumber() << " " << annotation << endl;
	
	//Hole* temp_holeptr = (Hole*) coreA1->getParent();
	//newSpliceHole->setType(temp_holeptr->getType());
	//newSpliceHole->setAnnotation((char*) temp_holeptr->getAnnotation());
	
	affinestatus = false;
	if (coreA1->getAffineStatus() == 1)
		affinestatus = true;
	coreptr->setDepthOffset(coreA2->getDepthOffset(), affinestatus);

	Value* lastvalue = NULL;
	bool temp_mode = tieptr->isConstrained();

	lastvalue = assignAboveValues(coreptr, coreA2, infoTiedA->m_valueptr, temp_mode, infoTiedA->m_mcd);
	
	// took data between  			
	bool append = false;
	bool startnew = false;	

	Value* tempValueptr = NULL;
	//int coretype;
	double gap;
	int values_size;
	Value* temp_newValue = NULL;

	// ------------ HYEJUNG ------------------------------------------------
				
	for(order=1; order < count; order++)
	{
		//cout << "order ---> " << order << " " << count << endl;
	
		tieptr = findTie(order);
		if(tieptr == NULL) 
		{
#ifdef DEBUG		
			std::cout << "[DEBUG]  could not find tie : " << order << std::endl;
#endif
			continue;
		}
	
		m_splicerties.push_back(tieptr);
		coreB1 = tieptr->getTieTo();
		coreB2 = tieptr->getTied();
		infoTieToB = tieptr->getInfoTieTo();
		infoTiedB = tieptr->getInfoTied();

		//cout << infoTiedB->m_valueptr->getTop() << " " << infoTieToB->m_valueptr->getTop() << endl;
		//cout << "-------- @@@ " << coreA1->getName() << coreA1->getNumber() << endl;
		//cout << "-------- @@@ " << coreB1->getName() << coreB1->getNumber() << endl;
					
		// took data between  
		if((tieptr->isAppend() == true) && tieptr->isAll() == false)
		{
			if((order== 1) && (count == 1)) break;			
			if (order == (count-1)) break;
			append = true;
			
			if(startnew == false) 
			{
				coreptr = newSpliceHole->createCore(noCore);
				noCore++;
				coretype = coreA1->getType();
				coreptr->setType(coretype);
				memset(annotation, 0, 25);
				sprintf(annotation, "%s%d", coreA1->getName(), coreA1->getNumber());
				coreptr->setAnnotation(&annotation[0]);
				//cout << "assignBelowValues-" << order << " annotation = " << annotation << endl;
				
				affinestatus = false;
				
				if (coreA1->getAffineStatus() == 1)
					affinestatus = true;
					
				coreptr->setDepthOffset(coreA1->getDepthOffset(), affinestatus);
				
				/*if(tieptr->isConstrained() == false)
				{
					//offset = tieptr->getOffset();
					//offset = offset - coreA1->getDepthOffset();
					cout << "false " << endl;
				} else 
				{
					cout << "true " << endl;
				}*/
				
				if(temp_mode == false)
				{
					//cout << "temp : false " << endl;
					offset = offset - coreA1->getDepthOffset();
				} else 
				{
					//cout << "temp :  true " << endl;
					offset = 0;
				}

				//cout << "----------------------------------- TEST " << tieptr->getOffset()  << " " << offset << " " <<  coreA1->getDepthOffset() << endl;
#ifdef DEBUG				
				if( infoTiedA->m_valueptr == NULL)
				{
					std::cout << "[DEBUG]  NULL" << std::endl;
				}
#endif				
				assignBelowValues(coreptr, coreA1, infoTieToA->m_valueptr, lastvalue, tieptr->isConstrained(), infoTieToA->m_mcd, offset);			
				offset = 0;
				
				startnew = true;
				coreA1 = coreB1;
				coreA2 = coreB2;
				infoTieToA = infoTieToB;
				infoTiedA = infoTiedB;	
				coreptr->updateRange();		
				continue;
			} else 
			{
				//cout << "append -------- " << coreA1->getName() << " " << noCore << endl;
				coreptr = newSpliceHole->createCore(noCore);
				if(coreptr != NULL)
				{
					noCore++;					
					coreptr->copy(coreA1);
					coreptr->setDepthOffset(coreA1->getDepthOffset());
					coreptr->setNumber(order);
					memset(annotation, 0, 25);
					sprintf(annotation, "%s%d", coreA1->getName(), coreA1->getNumber());
					coreptr->setAnnotation(&annotation[0]);
					
					// set.... source
					values_size = coreptr->getNumOfValues();
					for(int ith=0 ; ith < values_size; ith++) 
					{
						temp_newValue = coreptr->getValue(ith); 
						if(temp_newValue == NULL) continue;
						temp_newValue->setSource(coreA1->getValue(ith));
					}

					//cout << order << " annotation = " << annotation << endl;
					coreptr->updateRange();	
				}	
	
				coreA1 = coreB1;
				coreA2 = coreB2;
				infoTieToA = infoTieToB;
				infoTiedA = infoTiedB;	
				continue;
			}

		} else if((tieptr->isAppend() == true) && tieptr->isAll() == true)
		{
			if(append == true) 
			{
#ifdef DEBUG			
				std::cout << "true --- appended -----------" << std::endl;
#endif
				//startnew = false;
				//break;
				if((infoTieToB->m_top == 0.0f) && (infoTieToB->m_bottom <= -9999.0))
				{
					break;
				} 
			}
		}
		append = false;
		//cout << "2 ------>" <<   infoTiedA->m_valueptr->getELD() << endl;
		//cout << coreB1->getName() << coreB1->getNumber() << " " << coreB2->getName() << coreB2->getNumber() << endl;
	
		coreptr = newSpliceHole->createCore(noCore);
		noCore++;		
		coretype = coreB1->getType();
		coreptr->setType(coretype);
		memset(annotation, 0, 25);
		sprintf(annotation, "%s%d", coreB2->getName(), coreB2->getNumber());
		coreptr->setAnnotation(&annotation[0]);
		//cout << "assignBetweenValues-" << order << " annotation " << annotation << endl;
			
		affinestatus = false;
		if (coreB2->getAffineStatus() == 1)
			affinestatus = true;
		coreptr->setDepthOffset(coreB2->getDepthOffset(), affinestatus);
					
		if(startnew == true)
		{
			//cout << "startnew "  << coreptr->getName() << coreptr->getNumber() << " " << coreB2->getName() << coreB2->getNumber()  << "  " <<  coreB1->getName() << coreB1->getNumber()<< endl;
			lastvalue = assignAboveValues(coreptr, coreB2, infoTiedB->m_valueptr, tieptr->isConstrained(), infoTiedB->m_mcd);
			startnew = false;
			offset = tieptr->getOffset();
			//offset = 0;	
		} else
		{
			if(tieptr->isConstrained() == false)
			{
				//gap = infoTiedB->m_valueptr->getELD() - infoTiedA->m_valueptr->getMcd();
				//cout << "gap = " << gap << " " << infoTiedB->m_coreptr->getName() << infoTiedB->m_coreptr->getNumber() << endl;
				//tempValueptr = assignBetweenValues(coreB2, infoTieToA->m_valueptr, gap);
				tempValueptr =  infoTiedB->m_valueptr;
				if(temp_mode == true)
				{
					lastvalue = assignBetweenValues(coreptr, coreB2, infoTieToA->m_valueptr, tempValueptr, lastvalue, tieptr->isConstrained(), infoTieToA->m_mcd, 0);
				} else
				{ 
					lastvalue = assignBetweenValues(coreptr, coreB2, infoTieToA->m_valueptr, tempValueptr, lastvalue, tieptr->isConstrained(), infoTieToA->m_mcd, offset - coreB2->getDepthOffset());
				}
				offset = tieptr->getOffset();
			} else 
			{
				//std::cout << " depth " << infoTiedA->m_valueptr->getELD() << " " <<  infoTiedB->m_valueptr->getELD() << std::endl;
			
				if (temp_mode == false)
				{
					offset = offset - coreB2->getDepthOffset();
					// stop part need to change.... update : infoTiedB->m_valueptr....					
					tempValueptr = findValue(coreB2, infoTiedB->m_valueptr->getELD() - offset);
#ifdef DEBUG
					if(tempValueptr == NULL)
					{
						std::cout << "[Splice] Generate Splice : NULL Error " << std::endl;
					}
#endif
					//std::cout << " 2 depth " << infoTiedA->m_valueptr->getELD() << " " <<  tempValueptr->getELD() << std::endl;
					lastvalue = assignBetweenValues(coreptr, coreB2, infoTieToA->m_valueptr, tempValueptr, lastvalue, tieptr->isConstrained(), infoTieToA->m_mcd, offset);				
				} else 
				{
					lastvalue = assignBetweenValues(coreptr, coreB2, infoTieToA->m_valueptr, infoTiedB->m_valueptr, lastvalue, tieptr->isConstrained(), infoTieToA->m_mcd, 0);
				}
				offset = 0;
				//cout <<"-----------------constrained " << coreB2->getName() << coreB2->getNumber() << endl;
#ifdef DEBUG
				if(lastvalue == NULL) 
				{
					std::cout << "[Splice] Generate Splice : could not find tie assignBetweenValues : " << order << std::endl;
				}
#endif				
			}
		}

		temp_mode = tieptr->isConstrained();
		coreptr->updateRange();	
				
		// switch
		coreA1 = coreB1;
		coreA2 = coreB2;
		infoTieToA = infoTieToB;
		infoTiedA = infoTiedB;
	}
	
	m_tiepoint = lastvalue;
	
	
	if(tieptr != NULL)
	{
		//cout << "------------------> " <<endl;
		
		if (startnew == false)
		{
			//cout << "3 append -------- " << coreA1->getName() << coreA1->getNumber()  << endl;

			coreptr = newSpliceHole->createCore(noCore);
			noCore++;
			coretype = coreA1->getType();
			coreptr->setType(coretype);
			memset(annotation, 0, 25);
			sprintf(annotation, "%s%d", coreA1->getName(), coreA1->getNumber());
			coreptr->setAnnotation(&annotation[0]);
			//cout << " ------------ : "  << coreA1->getName() <<  coreA1->getNumber()  << " " << noCore -1 << annotation << endl;
									
			affinestatus = false;
			
			if (coreA1->getAffineStatus() == 1)
				affinestatus = true;
			
			coreptr->setDepthOffset(coreA1->getDepthOffset(), affinestatus);	
			//cout << "1 offset = " << offset << " " << coreA1->getDepthOffset() << " " << tieptr->getOffset() << endl;	
#ifdef DEBUG
			if( infoTieToA->m_valueptr == NULL)
			{
				std::cout << "[DEBUG] NULL" << std::endl;

			}
#endif			
			//cout << "2 " << infoTiedA->m_valueptr->getTop() << " " << infoTieToA->m_valueptr->getTop() << endl;

			if(temp_mode == false)
			{
				//cout << " temp mode : false " << endl;
				if(tieptr->isAppend() == true)
				{
					offset = offset - coreA1->getDepthOffset();
					assignBelowValues(coreptr, coreA1, infoTieToA->m_valueptr, lastvalue, tieptr->isConstrained(), infoTieToA->m_mcd, offset);
				} else 
				{
					offset = tieptr->getOffset();		
					offset = offset - coreA1->getDepthOffset();
					assignBelowValues(coreptr, coreA1, infoTieToA->m_valueptr, lastvalue, tieptr->isConstrained(), infoTieToA->m_mcd, offset);
				}
			} else 
			{
				//cout << " temp mode : true "  << coreptr->getName() << coreptr->getNumber() << " " <<  coreA1->getName() << coreA1->getNumber() << endl;
				if((tieptr->isAppend() == true)  && (tieptr->isAll() == false))
				{
					assignBelowValues(coreptr, coreA1, infoTieToA->m_valueptr, lastvalue, tieptr->isConstrained(), infoTieToA->m_mcd, 0);
				} else if((tieptr->isAppend() == true)  && (tieptr->isAll() == true))
				{ 
#ifdef DEBUG
					cout << lastvalue->getELD() << " "  << infoTieToA->m_valueptr->getELD() << " " << infoTiedA->m_valueptr->getELD() << endl;
#endif
					assignBelowValues(coreptr, coreA1, infoTieToA->m_valueptr, lastvalue, tieptr->isConstrained(), infoTieToA->m_mcd, 0);
				} else
				{ 
					assignBelowValues(coreptr, coreA1, infoTieToA->m_valueptr, lastvalue, tieptr->isConstrained(), infoTieToA->m_mcd, 0);
				}
			}
			coreptr->updateRange();	

		} else 
		{
			//cout << "4 append -------- " << coreA1->getName()  << endl;
			coreptr = newSpliceHole->createCore(noCore);
			if(coreptr != NULL)
			{
				noCore++;					
				coreptr->copy(coreA1);
				coreptr->setDepthOffset(coreA1->getDepthOffset());
				coreptr->setNumber(order);
				memset(annotation, 0, 25);
				sprintf(annotation, "%s%d", coreA1->getName(), coreA1->getNumber());
				coreptr->setAnnotation(&annotation[0]);
				
				// set.... source
				values_size = coreptr->getNumOfValues();
				for(int ith=0 ; ith < values_size; ith++) 
				{
					temp_newValue = coreptr->getValue(ith); 
					if(temp_newValue == NULL) continue;
					temp_newValue->setSource(coreA1->getValue(ith));
				}				
				//cout << "4. ----------append " << annotation << " " << coreA1->getType() << endl;
				coreptr->updateRange();	
			}		
		}
		
		if((tieptr->isAppend() == true) && (tieptr->isAll() == false)) 
		{

			//cout << "5 append -------- " << coreB1->getName()  << endl;
			coreptr = newSpliceHole->createCore(noCore);
			if(coreptr != NULL)
			{
				noCore++;					
				coreptr->copy(coreB1);
				coreptr->setDepthOffset(coreB1->getDepthOffset());
				coreptr->setNumber(order);
				memset(annotation, 0, 25);
				sprintf(annotation, "%s%d", coreB1->getName(), coreB1->getNumber());
				coreptr->setAnnotation(&annotation[0]);
				// set.... source
				values_size = coreptr->getNumOfValues();
				for(int ith=0 ; ith < values_size; ith++) 
				{
					temp_newValue = coreptr->getValue(ith); 
					if(temp_newValue == NULL) continue;
					temp_newValue->setSource(coreB1->getValue(ith));
				}					
				coreptr->updateRange();	
				//cout << "5. ----------append " << annotation << " " << coreB1->getType() << " " << coreptr->getType()  << endl;
			}
		} else if((tieptr->isAppend() == true) && (tieptr->isAll() == true)) 
		{
			//cout << "end part " << coreA1->getName()  << coreA1->getNumber() << endl;
			holeptr = m_dataptr->getHole((char*)coreA1->getName());
			if(holeptr != NULL)
			{
				int coreno = coreA1->getNumber();
				numCores = holeptr->getNumOfCores();
				for(coreno; coreno < numCores ; coreno++, order++)
				{
					coreptr= holeptr->getCore(coreno);
					if(coreptr == NULL) continue;
					coreA2 = newSpliceHole->createCore(noCore);
					if(coreA2 == NULL) continue;
					noCore++;
					coreA2->setDepthOffset(coreptr->getDepthOffset());
					coreA2->copy(coreptr);
					coreA2->setNumber(order);
					memset(annotation, 0, 25);
					sprintf(annotation, "%s%d", coreptr->getName(), coreptr->getNumber());
					coreA2->setAnnotation(&annotation[0]);	
					
					// set.... source
					values_size = coreptr->getNumOfValues();
					for(int ith=0 ; ith < values_size; ith++) 
					{
						temp_newValue = coreA2->getValue(ith); 
						if(temp_newValue == NULL) continue;
						temp_newValue->setSource(coreptr->getValue(ith));
					}
											
					coreA2->updateRange();	
				}
			}
		}

		
	}
	
	if(newSpliceHole)
	{
		newSpliceHole->update();
		/*std::cout << "created splice : number of cores : " << newSpliceHole->getNumOfCores() << std::endl;
		for(int i=0; i < newSpliceHole->getNumOfCores(); i++)
		{
			coreptr= newSpliceHole->getCore(i);
			std::cout << coreptr->getAnnotation() << " : " << coreptr->getNumOfValues() << std::endl;
		}*/
		
	}
	//cout << "[DEBUG] Generating Splice Hole is done" << endl;	

	//m_mainHole->debugPrintOut();
}


void Correlator::initiateAltSplice( void ) 
{
	if(m_dataptr == NULL) return;
	
	//data = "";
#ifdef DEBUG	
	cout << "[DEBUG] Initiating Alt Splice Hole" << endl;
#endif
	// how many real-tie
    int numHoles = m_dataptr->getNumOfHoles();
    int numCores, numTies;

    Hole* holeptr;
    Core* coreptr;
	Tie* tieptr;
	vector<Tie*> alt_tie_list;
	for(int i=0; i < numHoles; i++)
	{
		holeptr = m_dataptr->getHole(i);
        if(holeptr == NULL) continue;
        numCores =  holeptr->getNumOfCores();
        for(int j=0; j <= numCores; j++)
        {
			coreptr = holeptr->getCore(j);
            if(coreptr == NULL) continue;
			numTies = coreptr->getNumOfTies();
            for(int k=0; k < numTies; k++)
			{
               	tieptr = coreptr->getTie(k);
				if(tieptr->getType() == ALT_REAL_TIE)
				{
					alt_tie_list.push_back(tieptr);
				}
            }
			coreptr->deleteTies(ALT_REAL_TIE);
		}
	}
	
	vector<Tie*>::iterator iter;
	for(iter = alt_tie_list.begin(); iter != alt_tie_list.end(); iter++) 
	{
		tieptr = (Tie*) *iter;
		if(tieptr == NULL) continue; 
		delete tieptr;
		tieptr = NULL;
	}	
	
}

void Correlator::generateAltSpliceHole( string& data ) 
{
	if(m_dataptr == NULL) return;
	
	//data = "";
#ifdef DEBUG	
	cout << "[DEBUG] Generating Alt Splice Hole is started" << endl;
#endif
	// how many real-tie
    int numHoles = m_dataptr->getNumOfHoles();
    int numCores, numTies;

    Hole* holeptr;
    Core* coreptr;
	Tie* tieptr;
	int count=0;
	
	for(int i=0; i < numHoles; i++)
	{
		holeptr = m_dataptr->getHole(i);
        if(holeptr == NULL) continue;
        numCores =  holeptr->getNumOfCores();
        for(int j=0; j <= numCores; j++)
        {
			coreptr = holeptr->getCore(j);
            if(coreptr == NULL) continue;
			numTies = coreptr->getNumOfTies();
            for(int k=0; k < numTies; k++)
			{
               	tieptr = coreptr->getTie(k);
				if(tieptr->getType() == ALT_REAL_TIE)
				{
					count++;
				}
            }
		}
	}
	
	if (count == 0) return;
	int spliceOrder = count;
	
	int order = 0;
    Core* coreA1 = NULL;
    Core* coreA2 = NULL;
    Core* coreB1 = NULL;
    Core* coreB2 = NULL;
    TieInfo* infoTieToA = NULL;
    TieInfo* infoTiedA = NULL;
    TieInfo* infoTieToB = NULL;
    TieInfo* infoTiedB = NULL;
	bool affinestatus = false;

	Data* newDataptr = new Data();
	Hole* newSpliceHole = newDataptr->createHole(0, "X", USERDEFINEDTYPE);
	if (newSpliceHole == NULL) 
	{
#ifdef DEBUG	
		cout << "[ERROR] Could not create new splice hole" << endl;
#endif
		return;
	}
	newSpliceHole->setAnnotation("splice");
	newDataptr->setLeg((char*)m_dataptr->getLeg());
	newDataptr->setSite((char*)m_dataptr->getSite());
	
	
	//m_mainHole[0]->setParent(&m_correlatorData);

	double offset=0;
	int noCore = 0;
	// first tie is for above : 
	tieptr = findTie(order, true);
	if(tieptr == NULL) 
	{
#ifdef DEBUG	
		cout << "[DEBUG]  NULL" << endl;
#endif
		return;
	}
	
	if(tieptr->isConstrained() == false)
		offset = tieptr->getOffset();

    coreA1 = tieptr->getTieTo();
    coreA2 = tieptr->getTied();
    infoTieToA = tieptr->getInfoTieTo();
	infoTiedA = tieptr->getInfoTied();


	// took data for above
	coreptr = newSpliceHole->createCore(noCore);
	noCore++;
	int coretype = coreA1->getType();
	coreptr->setType(coretype);
	char annotation[25];
	memset(annotation, 0, 25);
	sprintf(annotation, "%s%d", coreA2->getName(), coreA2->getNumber());
	coreptr->setAnnotation(&annotation[0]);
	//cout << "annotation " << annotation << endl;
	
	affinestatus = false;
	if (coreA1->getAffineStatus() == 1)
		affinestatus = true;
	// ----- coreptr->setDepthOffset(coreA1->getDepthOffset(), affinestatus);
	coreptr->setDepthOffset(coreA2->getDepthOffset(), affinestatus);

	Value* lastvalue = NULL;
	bool temp_mode = tieptr->isConstrained();	
	lastvalue = assignAboveValues(coreptr, coreA2, infoTiedA->m_valueptr, temp_mode, infoTiedA->m_mcd);
	
	bool append = false;
	bool startnew = false;	

	Value* tempValueptr = NULL;
	//int coretype;
	double gap;

	
				
	for(order=1; order < count; order++)
	{
		//cout << "order ---> " << order << " " << count << endl;
	
		tieptr = findTie(order, true);
		if(tieptr == NULL) 
		{
#ifdef DEBUG		
			std::cout << "[DEBUG] could not find tie : " << order << std::endl;
#endif
			continue;
		}
	
		coreB1 = tieptr->getTieTo();
		coreB2 = tieptr->getTied();
		infoTieToB = tieptr->getInfoTieTo();
		infoTiedB = tieptr->getInfoTied();

		//cout << infoTiedB->m_valueptr->getTop() << " " << infoTieToB->m_valueptr->getTop() << endl;
		//cout << "-------- @@@ " << coreA1->getName() << coreA1->getNumber() << endl;
		//cout << "-------- @@@ " << coreB1->getName() << coreB1->getNumber() << endl;
					
		// took data between  
		if((tieptr->isAppend() == true) && tieptr->isAll() == false)
		{
			if((order== 1) && (count == 1)) break;			
			if (order == (count-1)) break;
			append = true;
			
			if(startnew == false) 
			{
				coreptr = newSpliceHole->createCore(noCore);
				noCore++;
				coretype = coreA1->getType();
				coreptr->setType(coretype);
				memset(annotation, 0, 25);
				sprintf(annotation, "%s%d", coreA1->getName(), coreA1->getNumber());
				coreptr->setAnnotation(&annotation[0]);
				//cout << "assignBelowValues-" << order << " annotation = " << annotation << endl;
				
				affinestatus = false;
				
				if (coreA1->getAffineStatus() == 1)
					affinestatus = true;
					
				coreptr->setDepthOffset(coreA1->getDepthOffset(), affinestatus);
				
				/*if(tieptr->isConstrained() == false)
				{
					//offset = tieptr->getOffset();
					//offset = offset - coreA1->getDepthOffset();
					cout << "false " << endl;
				} else 
				{
					cout << "true " << endl;
				}*/
				
				if(temp_mode == false)
				{
					//cout << "temp : false " << endl;
					offset = offset - coreA1->getDepthOffset();
				} else 
				{
					//cout << "temp :  true " << endl;
					offset = 0;
				}

				//cout << "----------------------------------- TEST " << tieptr->getOffset()  << " " << offset << " " <<  coreA1->getDepthOffset() << endl;
#ifdef DEBUG			
				if( infoTiedA->m_valueptr == NULL)
				{
					std::cout << "[DEBUG] NULL" << std::endl;
				}
#endif
				
				assignBelowValues(coreptr, coreA1, infoTieToA->m_valueptr, lastvalue, tieptr->isConstrained(), infoTieToA->m_mcd, offset);			
				offset = 0;
				
				startnew = true;
				coreA1 = coreB1;
				coreA2 = coreB2;
				infoTieToA = infoTieToB;
				infoTiedA = infoTiedB;			
				continue;
			} else 
			{
				//cout << "append -------- " << coreA1->getName() << " " << noCore << endl;
				coreptr = newSpliceHole->createCore(noCore);
				if(coreptr != NULL)
				{
					noCore++;					
					coreptr->copy(coreA1);
					coreptr->setDepthOffset(coreA1->getDepthOffset());
					coreptr->setNumber(order);
					memset(annotation, 0, 25);
					sprintf(annotation, "%s%d", coreA1->getName(), coreA1->getNumber());
					coreptr->setAnnotation(&annotation[0]);
					//cout << order << " annotation = " << annotation << endl;
				}	
	
				coreA1 = coreB1;
				coreA2 = coreB2;
				infoTieToA = infoTieToB;
				infoTiedA = infoTiedB;					
				continue;
			}

		} else if((tieptr->isAppend() == true) && tieptr->isAll() == true)
		{
			if(append == true) 
			{
				//cout << "true --- appended " << endl;
				//startnew = false;
				//break;
				if((infoTieToB->m_top == 0.0f) && (infoTieToB->m_bottom <= -9999.0))
				{
					break;
				} 
			}
		}
		append = false;
		//cout << "2 ------>" <<   infoTiedA->m_valueptr->getELD() << endl;
		//cout << coreB1->getName() << coreB1->getNumber() << " " << coreB2->getName() << coreB2->getNumber() << endl;
	
		coreptr = newSpliceHole->createCore(noCore);
		noCore++;		
		coretype = coreB1->getType();
		coreptr->setType(coretype);
		memset(annotation, 0, 25);
		sprintf(annotation, "%s%d", coreB2->getName(), coreB2->getNumber());
		coreptr->setAnnotation(&annotation[0]);
		//cout << "assignBetweenValues-" << order << " annotation " << annotation << endl;
			
		affinestatus = false;
		if (coreB2->getAffineStatus() == 1)
			affinestatus = true;
		coreptr->setDepthOffset(coreB2->getDepthOffset(), affinestatus);
					
		if(startnew == true)
		{
			//cout << "startnew "  << coreptr->getName() << coreptr->getNumber() << " " << coreB2->getName() << coreB2->getNumber()  << "  " <<  coreB1->getName() << coreB1->getNumber()<< endl;
			lastvalue = assignAboveValues(coreptr, coreB2, infoTiedB->m_valueptr, tieptr->isConstrained(), infoTiedB->m_mcd);
			startnew = false;
			offset = tieptr->getOffset();
			//offset = 0;	
		} else
		{
			if(tieptr->isConstrained() == false)
			{
				//gap = infoTiedB->m_valueptr->getELD() - infoTiedA->m_valueptr->getMcd();
				//cout << "gap = " << gap << " " << infoTiedB->m_coreptr->getName() << infoTiedB->m_coreptr->getNumber() << endl;
				//tempValueptr = assignBetweenValues(coreB2, infoTieToA->m_valueptr, gap);
				tempValueptr =  infoTiedB->m_valueptr;
				if(temp_mode == true)
				{
					lastvalue = assignBetweenValues(coreptr, coreB2, infoTieToA->m_valueptr, tempValueptr, lastvalue, tieptr->isConstrained(), infoTieToA->m_mcd, 0);
				} else
				{ 
					lastvalue = assignBetweenValues(coreptr, coreB2, infoTieToA->m_valueptr, tempValueptr, lastvalue, tieptr->isConstrained(), infoTieToA->m_mcd, offset - coreB2->getDepthOffset());
				}
				offset = tieptr->getOffset();
			} else 
			{
				//std::cout << " depth " << infoTiedA->m_valueptr->getELD() << " " <<  infoTiedB->m_valueptr->getELD() << std::endl;
			
				if (temp_mode == false)
				{
					offset = offset - coreB2->getDepthOffset();
					// stop part need to change.... update : infoTiedB->m_valueptr....					
					tempValueptr = findValue(coreB2, infoTiedB->m_valueptr->getELD() - offset);
#ifdef DEBUG	
					if(tempValueptr == NULL)
					{
						std::cout << "[Splice] Generate Splice : NULL Error " << std::endl;
					}
#endif					
					//std::cout << " 2 depth " << infoTiedA->m_valueptr->getELD() << " " <<  tempValueptr->getELD() << std::endl;
					lastvalue = assignBetweenValues(coreptr, coreB2, infoTieToA->m_valueptr, tempValueptr, lastvalue, tieptr->isConstrained(), infoTieToA->m_mcd, offset);				
				} else 
				{
					lastvalue = assignBetweenValues(coreptr, coreB2, infoTieToA->m_valueptr, infoTiedB->m_valueptr, lastvalue, tieptr->isConstrained(), infoTieToA->m_mcd, 0);
				}
				offset = 0;
				//cout <<"-----------------constrained " << coreB2->getName() << coreB2->getNumber() << endl;
#ifdef DEBUG				
				if(lastvalue == NULL) 
				{
					std::cout << "[Splice] Generate Splice : could not find tie assignBetweenValues : " << order << std::endl;
				}
#endif
			}
		}

		temp_mode = tieptr->isConstrained();

		// switch
		coreA1 = coreB1;
		coreA2 = coreB2;
		infoTieToA = infoTieToB;
		infoTiedA = infoTiedB;
	}
	
	m_tiepoint = lastvalue;
	
	
	if(tieptr != NULL)
	{
		//cout << "------------------> " <<endl;
		
		if (startnew == false)
		{
			//cout << "3 append -------- " << coreA1->getName() << coreA1->getNumber()  << endl;

			coreptr = newSpliceHole->createCore(noCore);
			noCore++;
			coretype = coreA1->getType();
			coreptr->setType(coretype);
			memset(annotation, 0, 25);
			sprintf(annotation, "%s%d", coreA1->getName(), coreA1->getNumber());
			coreptr->setAnnotation(&annotation[0]);
			//cout << " ------------ : "  << coreA1->getName() <<  coreA1->getNumber()  << " " << noCore -1 << annotation << endl;
									
			affinestatus = false;
			
			if (coreA1->getAffineStatus() == 1)
				affinestatus = true;
			
			coreptr->setDepthOffset(coreA1->getDepthOffset(), affinestatus);	
			//cout << "1 offset = " << offset << " " << coreA1->getDepthOffset() << " " << tieptr->getOffset() << endl;	
#ifdef DEBUG
			if( infoTieToA->m_valueptr == NULL)
			{
				std::cout << "[DEBUG]  NULL" << std::endl;

			}
#endif			
			
			//cout << "2 " << infoTiedA->m_valueptr->getTop() << " " << infoTieToA->m_valueptr->getTop() << endl;

			if(temp_mode == false)
			{
				//cout << " temp mode : false " << endl;
				if(tieptr->isAppend() == true)
				{
					offset = offset - coreA1->getDepthOffset();
					assignBelowValues(coreptr, coreA1, infoTieToA->m_valueptr, lastvalue, tieptr->isConstrained(), infoTieToA->m_mcd, offset);
				} else 
				{
					offset = tieptr->getOffset();		
					offset = offset - coreA1->getDepthOffset();
					assignBelowValues(coreptr, coreA1, infoTieToA->m_valueptr, lastvalue, tieptr->isConstrained(), infoTieToA->m_mcd, offset);
				}
			} else 
			{
				//cout << " temp mode : true "  << coreptr->getName() << coreptr->getNumber() << " " <<  coreA1->getName() << coreA1->getNumber() << endl;
				if((tieptr->isAppend() == true)  && (tieptr->isAll() == false))
				{
					assignBelowValues(coreptr, coreA1, infoTieToA->m_valueptr, lastvalue, tieptr->isConstrained(), infoTieToA->m_mcd, 0);
				} else if((tieptr->isAppend() == true)  && (tieptr->isAll() == true))
				{ 
					//cout << lastvalue->getELD() << " "  << infoTieToA->m_valueptr->getELD() << " " << infoTiedA->m_valueptr->getELD() << endl;
					assignBelowValues(coreptr, coreA1, infoTieToA->m_valueptr, lastvalue, tieptr->isConstrained(), infoTieToA->m_mcd, 0);
				} else
				{ 
					assignBelowValues(coreptr, coreA1, infoTieToA->m_valueptr, lastvalue, tieptr->isConstrained(), infoTieToA->m_mcd, 0);
				}
			}

		} else 
		{
			//cout << "4 append -------- " << coreA1->getName()  << endl;
			coreptr = newSpliceHole->createCore(noCore);
			if(coreptr != NULL)
			{
				noCore++;					
				coreptr->copy(coreA1);
				coreptr->setDepthOffset(coreA1->getDepthOffset());
				coreptr->setNumber(order);
				memset(annotation, 0, 25);
				sprintf(annotation, "%s%d", coreA1->getName(), coreA1->getNumber());
				coreptr->setAnnotation(&annotation[0]);
				//cout << "4. ----------append " << annotation << " " << coreA1->getType() << endl;
			}		
		}
		
		if((tieptr->isAppend() == true) && (tieptr->isAll() == false)) 
		{

			//cout << "5 append -------- " << coreB1->getName()  << endl;
			coreptr = newSpliceHole->createCore(noCore);
			if(coreptr != NULL)
			{
				noCore++;					
				coreptr->copy(coreB1);
				coreptr->setDepthOffset(coreB1->getDepthOffset());
				coreptr->setNumber(order);
				memset(annotation, 0, 25);
				sprintf(annotation, "%s%d", coreB1->getName(), coreB1->getNumber());
				coreptr->setAnnotation(&annotation[0]);
				//cout << "5. ----------append " << annotation << " " << coreB1->getType() << " " << coreptr->getType()  << endl;
			}
		} else if((tieptr->isAppend() == true) && (tieptr->isAll() == true)) 
		{
			//cout << "end part " << coreA1->getName()  << coreA1->getNumber() << endl;
			holeptr = m_dataptr->getHole((char*)coreA1->getName());
			if(holeptr != NULL)
			{
				int coreno = coreA1->getNumber();
				numCores = holeptr->getNumOfCores();
				for(coreno; coreno < numCores ; coreno++, order++)
				{
					coreptr= holeptr->getCore(coreno);
					if(coreptr == NULL) continue;
					coreA2 = newSpliceHole->createCore(noCore);
					if(coreA2 == NULL) continue;
					noCore++;
					coreA2->setDepthOffset(coreptr->getDepthOffset());
					coreA2->copy(coreptr);
					coreA2->setNumber(order);
					memset(annotation, 0, 25);
					sprintf(annotation, "%s%d", coreptr->getName(), coreptr->getNumber());
					coreA2->setAnnotation(&annotation[0]);	
				}
			}
		}

		
	}
	
	if(newSpliceHole)
	{
		newSpliceHole->update();
	}
	//cout << "[DEBUG] Generating Splice Hole is done" << endl;	

	//m_mainHole->debugPrintOut();

	data_range* range = newSpliceHole->getRange();
	char info[25];
	sprintf(info, "%.2f,%.2f,", range->mindepth, range->maxdepth);
	data = info;

	newSpliceHole->getTuple( data, SPLICEDATA);
	data += "#";
	
	delete newDataptr;
	newDataptr = NULL;
	
	vector<Tie*> alt_tie_list;	
	for(int i=0; i < numHoles; i++)
	{
		holeptr = m_dataptr->getHole(i);
        if(holeptr == NULL) continue;
        numCores =  holeptr->getNumOfCores();
        for(int j=0; j <= numCores; j++)
        {
			coreptr = holeptr->getCore(j);
            if(coreptr == NULL) continue;
			numTies = coreptr->getNumOfTies();
			//cout << coreptr->getName() << " " << coreptr->getNumber() << " " << numTies << endl;
            for(int k=0; k < numTies; k++)
			{
               	tieptr = coreptr->getTie(k);
				if(tieptr == NULL) continue;
				if(tieptr->getType() == ALT_REAL_TIE)
				{
					if(tieptr->getTied()->getId() == coreptr->getId())
						alt_tie_list.push_back(tieptr);
					coreptr->deleteTie(tieptr->getId());
				}
            }
			//coreptr->deleteTies(ALT_REAL_TIE);
		}
	}
	
	// delete alternative ties....	
	vector<Tie*>::iterator iter;
	for(iter = alt_tie_list.begin(); iter != alt_tie_list.end(); iter++) 
	{
		tieptr = (Tie*) *iter;
		if(tieptr == NULL) continue; 
		delete tieptr;
		tieptr = NULL;
	}	
#ifdef DEBUG	
	cout << "[DEBUG] Generating Alt Splice Hole is done" << endl;	
#endif			
	//m_mainHole->debugPrintOut();
}


void Correlator::setAgeSeries(int idx, double depth, char* code)
{
	if(m_dataptr == NULL) return;
	
	int numHoles = m_dataptr->getNumOfHoles();
	int numCores, numStrats;
	Hole* holeptr;
	Core* coreptr;
	Strat* stratptr;
		
	if(idx == 0)
	{
		for(int i=0; i < numHoles; i++)
		{
			 holeptr = m_dataptr->getHole(i);
			 if(holeptr == NULL) continue;
			 numCores =  holeptr->getNumOfCores();
			 for(int j=0; j < numCores; j++)
			 {
					coreptr = holeptr->getCore(j);
					if(coreptr == NULL) continue;
					numStrats = coreptr->getNumOfStrat();
					//cout << coreptr->getName() << coreptr->getNumber() <<  " numStrats " << numStrats << endl;
					for(int k=0; k < numStrats; k++)
					{
							stratptr = coreptr->getStrat(k);
							if(stratptr == NULL) continue;
							stratptr->setOrder(-1);
							//cout << stratptr->getCode() << " " << code << " " << stratptr->getTopMbsf() << " " << depth << endl;
							if((strcmp(stratptr->getCode(), code) == 0) && (fabs(stratptr->getTopMbsf() - depth) < 0.01))
							{
								stratptr->setOrder(0);
							}
					}
			 }
		}	
	} else 
	{
		for(int i=0; i < numHoles; i++)
		{
			 holeptr = m_dataptr->getHole(i);
			 if(holeptr == NULL) continue;
			 numCores =  holeptr->getNumOfCores();
			 for(int j=0; j < numCores; j++)
			 {
					coreptr = holeptr->getCore(j);
					if(coreptr == NULL) continue;
					numStrats = coreptr->getNumOfStrat();
					for(int k=0; k < numStrats; k++)
					{
							stratptr = coreptr->getStrat(k);
							if((strcmp(stratptr->getCode(), code) == 0) && (fabs(stratptr->getTopMbsf() - depth) < 0.01))
							{	
								//cout << "found ---- " << idx << endl;
								stratptr->setOrder(idx);
								return;
							}
					}
			 }
		}	
	}
}
	
void Correlator::getTuple( string& data, int type ) 
{
	Hole* holeptr = m_mainHole[0];
	
	if(type == LOG)
	{
		 holeptr = m_mainHole[1];
		 type = DATA;
	}
	else if(type == LOGSMOOTH)
	{
		 holeptr = m_mainHole[1];
		 type = LOGSMOOTH;
	}
	if(holeptr) 
	{
		data_range* range = m_dataptr->getRange();
		char info[25];
		sprintf(info, "%.2f,%.2f,", range->mindepth, range->maxdepth);
		data = info;

		holeptr->getTuple( data, type);
       	data += "#";
	}
}

void Correlator::getTuple( std::string& data, int hole_no, int type )
{
	int numHoles = m_dataptr->getNumOfHoles();	
	Hole* holeptr= NULL;
	for(int i=0; i < numHoles; i++)
	{
		holeptr = m_dataptr->getHole(i);
		if(holeptr == NULL) continue;
		if(i == hole_no)
		{
			data_range* range = m_dataptr->getRange();
			char info[25];
			sprintf(info, "%.2f,%.2f,", range->mindepth, range->maxdepth);
			data = info;

			holeptr->getTuple( data, type);
			data += "#";
		
			break;
		}
	}
}	

void Correlator::getSaganTuple( string& data, int fileflag ) 
{
	vector<Tie*>::iterator iter;
	Tie* tieptr = NULL;
	//cout << "m_saganties = " << m_saganties.size() << endl;
	//cout << "m_sagantotalties = " << m_sagantotalties.size() << endl;
	
	/*if (fileflag == false)
	{
		for(iter = m_saganties.begin(); iter != m_saganties.end(); iter++)
		{
			tieptr = (Tie*) *iter;
			if(tieptr)
			{
				if (tieptr->getSharedFlag() == false)
					tieptr->getTuple(data, SAGAN_TIE);
			}
		}
		if(m_saganties.size() > 0)
				data += "#";
	} else 
	{
		for(iter = m_sagantotalties.begin(); iter != m_sagantotalties.end(); iter++)
		{
			tieptr = (Tie*) *iter;
			if(tieptr)
			{
				if (tieptr->getSharedFlag() == false)
					tieptr->getTuple(data, SAGAN_TIE);
			}
		}	
		if(m_sagantotalties.size() > 0)
				data += "#";	
	}*/
	for(iter = m_sagantotalties.begin(); iter != m_sagantotalties.end(); iter++)
	{
		tieptr = (Tie*) *iter;
		if(tieptr)
		{
			if (tieptr->getSharedFlag() == false)
				tieptr->getTuple(data, SAGAN_FIXED_TIE);
		}
	}	
	if(m_sagantotalties.size() > 0)
			data += "#";	

	/*if(m_mainHole[0]) 
	{
		m_mainHole[0]->getTuple(data, DATA);
        	data += "#";
	}*/
}

void Correlator::getSpliceTuple( string& data ) 
{
	vector<Tie*>::iterator iter;
	Tie* tieptr = NULL;
	int coreno, numCores;
	Hole* holeptr = NULL;
	Core* coreptr = NULL;
	Core* coreA= NULL;
	char info[125];
	char* annotation = NULL;
	//cout << "m_splicerties = " << m_splicerties.size() << endl;
	
	for(iter = m_splicerties.begin(); iter != m_splicerties.end(); iter++)
	{
		tieptr = (Tie*) *iter;
		if(tieptr)
		{
			tieptr->getTuple(data, SPLICE);
		}
		
		if((tieptr->isAppend() == true) && (tieptr->isAll() == true)) 
		{
			coreA = tieptr->getTieTo();
			holeptr = m_dataptr->getHole((char*)coreA->getName());
			if(holeptr != NULL)
			{
				//cout << coreA->getName() << endl; 
				coreno = coreA->getNumber();
				//coreno++;
				numCores = holeptr->getNumOfCores();
				for(coreno; coreno < numCores ; coreno++)
				{
					coreptr= holeptr->getCore(coreno);
					if(coreptr != NULL)
					{
						annotation = (char*) coreptr->getParent()->getAnnotation();
						//cout << coreptr->getName() << coreno << endl;
						if(annotation == NULL)
							sprintf(info, "%d,%d,-,%s,%d,%f,%d,-,%s,%d,%f,:", -1, coreptr->getType(), coreptr->getName(), coreptr->getNumber(), 0.0f, coreptr->getType(), coreptr->getName(), coreptr->getNumber(), 0.0f);
						else 
							sprintf(info, "%d,%d,%s,%s,%d,%f,%d,%s,%s,%d,%f,:", -1, coreptr->getType(), annotation, coreptr->getName(), coreptr->getNumber(), 0.0f, coreptr->getType(), annotation, coreptr->getName(), coreptr->getNumber(), 0.0f);
						//std::cout << info << std::endl;
						data += info;	
					}
				}
			}		
		}

	} 
	
	if(m_splicerties.size() > 0)
        	data += "#";

	/*if(m_mainHole[0]) 
	{
		m_mainHole[0]->getTuple( data, DATA);
        	data += "#";
	}*/
}

void Correlator::getCoefList( string& data )
{
        char info[25];
        int size = m_coeflist.size();
        for(int i =0; i < size; i++)
        {
                sprintf(info, "%.4f,", m_coeflist[i]);
                data += info;
        }
}

void Correlator::squish(char* hole, int coreid, double squish )
{
        if(m_dataptr == NULL) return;

        Core* coreptr = findCore(hole, coreid);

        if(coreptr == NULL)
	{
#ifdef DEBUG
                cout << "[Squish] Error : can not find core" << endl;
#endif
	}
	
	coreptr->setStretch(squish);
#ifdef DEBUG
	cout << "[Squish] hole " << coreptr->getName() << " core " << coreptr->getNumber() << "  stretch/compress : " <<   coreptr->getStretch() << endl;
#endif	

}

void Correlator::squish( int coreid, double squish )
{
	if(m_dataptr == NULL) return;

	Core* coreptr = findCore(coreid);	
	if(coreptr == NULL) return;
	
	coreptr->setStretch(squish);
#ifdef DEBUG
	cout << "[Squish] hole " << coreptr->getName() << " core " << coreptr->getNumber() << "  stretch/compress : " <<   coreptr->getStretch() << endl;
#endif	
}

void Correlator::interporlate()
{
	// INTERPOLATED_TIED
//////
/*
  int i, j, k, n;
  double coredepth1, corevalue1, coredepth2, corevalue2;

  n = data[ds]->holes[h]->core[c]->numgood;
  if(n < 2) {
    return 1;
  }
  *place = -1;
  if(dep < data[ds]->holes[h]->core[c]->value[data[ds]->holes[h]->core[c]->good[0]]->mbsf ||
     dep > data[ds]->holes[h]->core[c]->value[data[ds]->holes[h]->core[c]->good[n-1]]->mbsf) {
    return 1;
  }
  for(i=0; i<n-1; ++i) {
    j = data[ds]->holes[h]->core[c]->good[i];
    k = data[ds]->holes[h]->core[c]->good[i+1];
    coredepth1 = data[ds]->holes[h]->core[c]->value[j]->mbsf;
    coredepth2 = data[ds]->holes[h]->core[c]->value[k]->mbsf;
    if(dep >= coredepth1 && dep <= coredepth2) {
      if(sm == YES) {
        corevalue1 = data[ds]->holes[h]->core[c]->value[j]->sm_data;;
        corevalue2 = data[ds]->holes[h]->core[c]->value[k]->sm_data;;
      }
      else if(sm == NO) {
        corevalue1 = *data[ds]->holes[h]->core[c]->value[j]->data;
        corevalue2 = *data[ds]->holes[h]->core[c]->value[k]->data;
      }
      else {
        return 1;
      }
      *val = corevalue1 + (corevalue2 - corevalue1)/(coredepth2 - coredepth1) * (dep - coredepth1);
      *place = j;
      break;
    }
  }*/
/////////////	

}

void Correlator::makeUpELD( void )
{
	if(m_dataptr == NULL) return;

	Hole* log_hole = NULL;
	Core* logcoreptr = NULL;	
	if(m_logdataptr)
	{
		log_hole = m_logdataptr->getHole(0);
		if(log_hole)
		{
			logcoreptr = log_hole->getCore(0);
		}
		if(logcoreptr == NULL) return;
	} else 
		return;
						
	int numHoles = m_dataptr->getNumOfHoles();
	int numCores, numTies;
			
	Tie* tieptr;
	Hole* holeptr;
	Core* coreptr;
	Value* valueptr;
	Value* valueTiedptr;
	TieInfo* infoTied = NULL;
	TieInfo* infoTieTo = NULL;
	data_range rangeA;

	std::vector<Tie*>::iterator iter;	
	std::vector<Tie*> temp_list;
	Tie* tieptrA = NULL;	
	TieInfo* infoTieToA = NULL;
	TieInfo* infoTiedA = NULL;
	int success = 0;	
	
	double rate=1.0f;
	double b = 0.0f;
	double gab;
	double tie_gab = 0.0f;
	bool morecoresflag = false;
	if(m_splicerties.size() > 0)
	{
		morecoresflag = true;
	}

	m_sagantotalties.clear();
	temp_list.clear();
	
	for(int i=0; i < numHoles; i++)
	{
		holeptr = m_dataptr->getHole(i);
		if(holeptr == NULL) continue;
		numCores = holeptr->getNumOfCores();
		for(int j=0; j < numCores; j++)
		{
			coreptr = holeptr->getCore(j);
			if(coreptr == NULL) continue;
			numTies = coreptr->getNumOfTies(SAGAN_FIXED_TIE);
#ifdef DEBUG
			if(numTies > 0)
			{
				cout << "[makeUpELD] number of Ties for Core No." << coreptr->getNumber() << " : " << numTies << endl;
			}
#endif			
			
			for(int k=0; k < numTies; k++)
			{
				tieptr = coreptr->getTie(SAGAN_FIXED_TIE, k);
				infoTied = tieptr->getInfoTied();
				if(infoTied == NULL) 
				{
#ifdef DEBUG				
					cout << "[DEBUG] ERROR : Could not find Tied information " << endl;
#endif
					continue;
				}

				if(temp_list.size() == 0)
				{
					temp_list.push_back(tieptr);
				} else
				{
					tieptrA = NULL;	
					infoTieToA = NULL;
					success = 0;
					for(iter = temp_list.begin(); iter != temp_list.end(); iter++)
					{
						tieptrA = (Tie*) *iter;
						if(tieptrA)
						{
							infoTiedA = tieptrA->getInfoTied();
							if(infoTiedA) 
							{
								if(infoTiedA->m_mcd > infoTied->m_mcd) 
								{
									temp_list.insert(iter, tieptr);
									success = 1;
									break;
								}
							}
						}
					}
					if(success == 0)
					{
						temp_list.push_back(tieptr);
					}
				}
			}
		}
	}
	
	for(int i=0; i < numHoles; i++)
	{
		holeptr = m_dataptr->getHole(i);
		if(holeptr == NULL) continue;

		numCores =  holeptr->getNumOfCores();		
		for(int j=0; j <= numCores; j++)
		{
			coreptr = holeptr->getCore(j);
			if(coreptr == NULL) continue;
					
			numTies = coreptr->getNumOfTies(SAGAN_FIXED_TIE);
			for(int k=0; k <= numTies; k++)
			{
				tieptr = coreptr->getTie(SAGAN_FIXED_TIE, k);
				if(tieptr == NULL) continue;
				
				infoTied = tieptr->getInfoTied();
				if(tieptr->getSharedFlag() == false)
				{
					for(iter = temp_list.begin(); iter != temp_list.end(); iter++)
					{
						tieptrA = (Tie*) *iter;
						if(tieptrA == NULL) continue; 
						
						infoTiedA = tieptrA->getInfoTied();
						if(infoTied->m_eld ==  infoTiedA->m_eld)
						{
							if(tieptrA != tieptr) 
								tieptr->addRefCount();
						}
					}
				}
			}
		}
	}	

	Value* temp_value;
	int idx;
	Value* test_Value;
	double temp_data, temp_top, offset, calc_depth;
	for(iter = temp_list.begin(); iter != temp_list.end(); iter++)
	{
		tieptr = (Tie*) *iter;
		if(tieptr == NULL) continue; 
		
		if(tieptr->getSharedFlag() == false)
		{
			m_isCoreOnly = true;
			if(tieptr->getRefCount() > 0)
				m_isCoreOnly = false;
			
			infoTied = tieptr->getInfoTied();
			if(infoTied == NULL) continue;

			// Add Interpolated Value.... with mbsf 
			temp_value = findValueWithMbsf(infoTied->m_coreptr, infoTied->m_mbsf);
			if(temp_value)
			{
				if(infoTied->m_mbsf != temp_value->getMbsf())
				{
					idx = temp_value->getNumber();
					test_Value = NULL;
					if(infoTied->m_mbsf < temp_value->getMbsf())
					{
						test_Value = infoTied->m_coreptr->getValue(idx-1);
						if(test_Value)
						{
							// 
							temp_data= getMbsfData(test_Value, temp_value, infoTied->m_mbsf); 
							temp_top = test_Value->getTop() + (infoTied->m_mbsf - test_Value->getMbsf()) * 100;
						}
					} else 
					{
						test_Value = infoTied->m_coreptr->getValue(idx+1);
						if(test_Value)
						{
							temp_data= getMbsfData(temp_value, test_Value, infoTied->m_mbsf); 
							temp_top = temp_value->getTop() + (infoTied->m_mbsf - temp_value->getELD()) * 100;
						}
					}
					
					offset = infoTied->m_coreptr->getDepthOffset();
					calc_depth = infoTied->m_mbsf;				

					test_Value = infoTied->m_coreptr->createInterpolatedValue(calc_depth);
					if(test_Value && (test_Value->getMbsf() != calc_depth))
					{
						if(temp_value->getQuality() != GOOD)  continue;
						
						test_Value->copy(temp_value);
						test_Value->setValueType(INTERPOLATED_VALUE);
						test_Value->setDepth(calc_depth);
						
						test_Value->applyAffine(offset, test_Value->getType());
						
						// need to update data and bottom/top value
						test_Value->setRawData(temp_data);
						test_Value->setTop(temp_top);
						test_Value->update();
						temp_value = test_Value;
					}
				}
				
			} else {
#ifdef DEBUG			
				std::cout << "[makeUpELD ERROR]  could not find value " << (char*)infoTied->m_coreptr->getName() <<  infoTied->m_coreptr->getNumber() << " (mbsf=" << infoTied->m_mbsf << ")" << std::endl;
#endif
			}
			
			// HYEJUNG
			//sagan(-1, "-", 0, infoTied->m_eld, (char*)infoTied->m_coreptr->getName(), infoTied->m_coreptr->getNumber(), infoTied->m_mcd);
			sagan(-1, "-", 0, infoTied->m_eld, (char*)infoTied->m_coreptr->getName(), infoTied->m_coreptr->getNumber(), temp_value->getELD());

			generateSagan();				
		}
	}


	for(iter = temp_list.begin(); iter != temp_list.end(); iter++)
	{
		tieptr = (Tie*) *iter;
		if(tieptr == NULL) continue; 
		
		infoTied = tieptr->getInfoTied();
		infoTied->m_coreptr->deleteTie(tieptr->getId());
		delete tieptr;
		tieptr = NULL;
	}
	temp_list.clear();

	//generateSagan();	
	
	//m_dataptr->update();
}

void Correlator::updateSaganTies(void)
{
	if(m_mainHole[0] == NULL) return;
	Core* coreptr = m_mainHole[0]->getCore(0);
	if(coreptr == NULL) return;	

	Tie* tieptr;
	std::vector<Tie*>::iterator iter;

	//sagan();
	
	char name[4];

	TieInfo* infoTied = NULL;
	int count =0;
	//cout << "update sagan tie = " << m_sagantotalties.size() << " " << m_saganties.size() << endl;
	for(iter = m_sagantotalties.begin(); iter != m_sagantotalties.end(); iter++)
	{
		tieptr = (Tie*) *iter;

		infoTied = tieptr->getInfoTied();
		if(infoTied->m_coreptr == NULL) continue;
		sprintf(name, "%s%d", infoTied->m_coreptr->getName(), infoTied->m_coreptr->getNumber());
		if(strcmp(name, coreptr->getParent()->getAnnotation()) == 0)
		{
			//cout << infoTied->m_coreptr->getName() << infoTied->m_coreptr->getNumber() << " " << coreptr->getAnnotation() <<  endl;
			tieptr->setType(SAGAN_TIE);
			m_saganties.push_back(tieptr);
			//m_sagantotalties.erase(iter);
			//iter--;
			
			count++;			
		}

	}

	if(count > 0)
	{
		const char*  annotation = coreptr->getParent()->getAnnotation();
		strcpy(name, annotation);
		char hole = name[0];
		int coreid = atoi(&name[1]);
		//cout << "hole = " << hole << " id = " << coreid << endl;
		coreptr = findCore(&hole, coreid);
		if(coreptr == NULL) return;
		int coresize = coreptr->getNumOfValues();
		Value* valueptr = NULL;
		for(int i=0; i < coresize; i++)
		{
			valueptr = coreptr->getValue(i);
			if(valueptr == NULL) continue;
			valueptr->resetELD();
			//cout << "inside " << coreptr->getName() << coreptr->getNumber() << " " << i << endl;
		}
		generateSagan();
	}
}
	

int Correlator::sagan(int tieindex, char* holeA, int coreidA, double posA, char* holeB, int coreidB, double posB)
{
#ifdef DEBUG
	std::cout << "[DEBUG] sagan : pos A = " << posA << " pos B = " << posB << std::endl;
#endif
	
	Hole* log_hole = NULL;
	Core* logcoreptr = NULL;
	TieInfo* infoTied = NULL;
	bool update = false;
	Tie* tieptr = NULL;
	Tie* tempTieptr;
	std::vector<Tie*>::iterator iter;
	for(iter = m_sagantotalties.begin(); iter != m_sagantotalties.end(); iter++)
	{
		tempTieptr = (Tie*) *iter;
		//if(tempTieptr->getId() == tieindex)
		if((tempTieptr->getSharedFlag() == false) && (tempTieptr->getId() == tieindex))
		{
			tieptr = tempTieptr;
			infoTied = tieptr->getInfoTied();
			holeB = (char*) infoTied->m_coreptr->getName();
			coreidB = infoTied->m_coreptr->getNumber();
#ifdef DEBUG			
			cout << "[DEBUG] found it " << tieindex << " " << holeB << coreidB << endl;
#endif
			update = true;
			break;
		}
	}
	
	//cout << "posA = " << posA << " posB = " << posB << endl;
	//cout << "A = " << holeA << coreidA << " B = " << holeB << coreidB << endl;

	if(m_logdataptr)
	{
		log_hole = m_logdataptr->getHole(0);
		if(log_hole)
		{
			logcoreptr = log_hole->getCore(0);
		}
		if(logcoreptr == NULL) return 0;
	} else 
		return 0;

    Core* maincoreptr = NULL;
    //Core* coreptr = NULL;
	//maincoreptr = findCore(holeB, coreidB);
	//if(maincoreptr == NULL) return 0;
	Value* valueB = NULL;
	Value* valueptr = NULL;
	string annot ="";
	char hole_B[10];
	int annot_len;
	if(tieptr != NULL)
	{
		// CHECK
		valueptr = tieptr->getTieToValue();
		if(valueptr && valueptr->getValueType() == INTERPOLATED_VALUE)
		{
			tieptr->getTieTo()->deleteInterpolatedValue(valueptr->getNumber());
		}
		
		valueB = tieptr->getTiedValue();
	} else 
	{
		if(m_mainHole[1] == NULL)
			valueB = findValueInHole(m_mainHole[0], posB);
		else 
			valueB = findValueInHole(m_mainHole[1], posB);
	}
	
	maincoreptr = findCore(holeB, coreidB);
	if(maincoreptr == NULL) 
	{
#ifdef DEBUG	
		cout << "[DEBUG] out " << holeB << coreidB << endl;
#endif
		return 0;
	}
	
	memset(hole_B, 0, 10);
	sprintf(hole_B, "%s %d", maincoreptr->getName(), maincoreptr->getNumber());
	m_sagan_corename = hole_B;	
	

	// calculate all inforamtion : top/bottom...
	// top, bottom
	data_range rangeA, rangeB;
	rangeA.top = posA;
	rangeB.top = posB;
	rangeA.bottom = rangeA.top;
	rangeB.bottom = rangeB.top;

	// find value.....
	Value* valueA = findValue(logcoreptr, rangeA.top);
	if(valueA == NULL)
	{
#ifdef DEBUG	
		cout << "[DEBUG] could not find value A" << endl;
#endif
		return 0;
	}

	double offset;
	double calc_depth;
	double temp_data;
	double temp_top;
	int idx;
	Value* test_Value = NULL;
		
	if(posA != valueA->getELD())
	{
		idx = valueA->getNumber();
		test_Value = NULL;

		if(posA < valueA->getELD())
		{
			test_Value = logcoreptr->getValue(idx-1);
			if(test_Value)
			{
				temp_data= getELDData(test_Value, valueA, posA); 
				temp_top = test_Value->getTop() + (posA - test_Value->getELD()) * 100;
			}				
		} else 
		{
			test_Value = logcoreptr->getValue(idx+1);
			if(test_Value)
			{
				temp_data= getELDData(valueA, test_Value, posA); 
				temp_top = valueA->getTop() + (posA - valueA->getELD()) * 100;
			}				
		}

		offset = logcoreptr->getDepthOffset();
		calc_depth = posA- offset;
		test_Value = logcoreptr->createInterpolatedValue(calc_depth);
		if(test_Value && (test_Value->getMbsf() != calc_depth))
		{
			test_Value->copy(valueA);
			test_Value->setValueType(INTERPOLATED_VALUE);
			test_Value->setDepth(calc_depth);
			
			test_Value->applyAffine(offset, test_Value->getType());
			//test_Value->setB(offset);
			
			// need to update data and bottom/top value
			test_Value->setRawData(temp_data);
			test_Value->setTop(temp_top);
			valueA = test_Value;
#ifdef DEBUG			
			std::cout << "[DEBUG/sagan] valueA value = "  << valueA->getELD() << " " << offset << " " << logcoreptr->getMudLine() << std::endl;
#endif			
			//std::cout << "offset = " << offset  << " stretch= " << test_Value->getStretch() << " B=" << test_Value->getB() << std::endl;
			//std::cout << "--> new value is created.... "  <<  posA << " " << valueA->getTop() << " " << valueA->getMbsf() << ", " << valueA->getMcd() << " " << valueA->getELD() << std::endl;
		}
	}
		
	test_Value = NULL;
			
	//cout << "top = " << rangeB.top << " " << holeB << coreidB << endl;
	valueB = findValue(maincoreptr, rangeB.top);
	if(valueB == NULL)
	{
#ifdef DEBUG	
		cout << "[DEBUG/sagan] could not find value B" << endl;
#endif
		return 0;
	}
	
	if(posB != valueB->getELD())
	{
		idx = valueB->getNumber();
		test_Value = NULL;

		if(posB < valueB->getELD())
		{
			test_Value = maincoreptr->getValue(idx-1);
			if(test_Value)
			{
				temp_data= getELDData(test_Value, valueB, posB); 
				temp_top = test_Value->getTop() + (posB - test_Value->getELD()) * 100;
			}				
		} else 
		{
			test_Value = maincoreptr->getValue(idx+1);
			if(test_Value)
			{
				temp_data= getELDData(valueB, test_Value, posB); 
				temp_top = valueB->getTop() + (posB - valueB->getELD()) * 100;
			}				
		}

		offset = maincoreptr->getDepthOffset();
		calc_depth = valueB->calcDepthWithELD(posB);
		
		test_Value = maincoreptr->createInterpolatedValue(calc_depth);
		if(test_Value && (test_Value->getMbsf() != calc_depth))
		{
			test_Value->copy(valueB);
			test_Value->setValueType(INTERPOLATED_VALUE);
			test_Value->setDepth(calc_depth);
			
			test_Value->applyAffine(offset, test_Value->getType());
			
			// need to update data and bottom/top value
			test_Value->setRawData(temp_data);
			test_Value->setTop(temp_top);
			valueB = test_Value;
#ifdef DEBUG					
			std::cout << "[DEBUG/sagan] valueB value = "  << valueB->getELD() << " " << valueB->getMcd() <<  " " << maincoreptr->getName() << maincoreptr->getNumber() << std::endl;
#endif
			//std::cout << "offset = " << offset << " stretch= " << test_Value->getStretch() << " B=" << test_Value->getB() << std::endl;
			//std::cout << "--> new value is created.... "  <<  posB << " " << valueB->getTop() << " " << valueB->getMbsf() << ", " << valueB->getMcd() << " " << valueB->getELD() << std::endl;
		}
	}
	
	m_tiepoint = valueA;
	rangeA.top = valueA->getTop();
	rangeA.bottom = rangeA.top;
	rangeB.top = valueB->getTop();
	rangeB.bottom = rangeB.top;
	//posB = valueB->getELD();
	//cout << " -- " << maincoreptr->getName() << maincoreptr->getNumber() << " depth (a, b)= " << valueA->getELD() << " , " << valueB->getELD() << endl;
	
	// create Tie and register.......
	//Tie* tieptr = new Tie(SAGAN_TIE);
	//if(tieptr == NULL) return NULL;
	if(tieptr == NULL)
	{
		tieptr = new Tie(SAGAN_TIE);
	}
	
	if (posA == posB)
	{
		tieptr->setStrightFlag(true);
	} else 
	{
		tieptr->setStrightFlag(false);
	}
	if (update == false)
	{ 
		tieptr->setTieTo(logcoreptr, valueA->getType(), valueA->getSection(), rangeA, valueA->getMbsf(), posA);
		tieptr->setTieTo(valueA);

		tieptr->setTied(maincoreptr, valueB->getType(), valueB->getSection(), rangeB, valueB->getMbsf(), posB);
		tieptr->setTied(valueB);
	} 
	
	unsigned int ret = tieptr->getId();
	int size = 0;
	valueptr = NULL;
	int extra_size=0;
	
	// if sagan option is for all
	char* hole_ptr;		
	
	Tie* tieptrA;
	infoTied = NULL;
	TieInfo* infoTiedA = NULL;
	int success;
	Tie* temp_tieptr = NULL;

	int numHoles;
	int numCores, numTies;
	Hole* extra_holeptr;
	Core* extra_coreptr;
	Tie* extra_tieptr;
	Value* extra_valueptr;
	std::vector<Tie*> temp_saganties;
	int numValues = 0;
	
	
	if(update == false)
	{
		maincoreptr->addTie(tieptr);
				
		if(m_isCoreOnly == false)
		{	
			numHoles = m_dataptr->getNumOfHoles();
			for(int i=0; i < numHoles; i++)
			{
				extra_holeptr = m_dataptr->getHole(i);
				if(extra_holeptr == NULL) continue;
				hole_ptr = (char*) extra_holeptr->getName();
				if(strcmp(hole_ptr, holeB) == 0) continue;

				extra_coreptr = extra_holeptr->getCore(posB, 1.0);
				//cout << extra_holeptr->getName() << " " << posB << endl;
				if(extra_coreptr == NULL) continue;
				
				extra_valueptr = NULL;
				if((extra_coreptr->getMinDepth() <= posB) && (extra_coreptr->getMaxDepth() >= posB))
				{
					extra_valueptr = findValue(extra_coreptr, posB);
				}
///////////
// HEEEEEEEEEEEE

				if(extra_valueptr == NULL)
				{
					numValues = 0;
					if(extra_coreptr->getValue(0)->getELD() < posB)
					{
						numValues = extra_coreptr->getNumOfValues() -1;
					}
					extra_valueptr = extra_coreptr->getValue(numValues);
					offset = extra_coreptr->getDepthOffset();
					calc_depth = extra_valueptr->calcDepthWithELD(posB);
					test_Value = extra_coreptr->createInterpolatedValue(calc_depth);
					if(test_Value && (test_Value->getMbsf() != calc_depth))
					{
							if(extra_valueptr->getQuality() != GOOD)  continue;

							test_Value->copy(extra_valueptr);
							test_Value->setValueType(INTERPOLATED_VALUE);
							test_Value->setDepth(calc_depth);
							test_Value->applyAffine(offset, test_Value->getType());
							extra_valueptr = test_Value;	
#ifdef DEBUG							
							std::cout << "[DEBUG/sgan] extra value(null) = "  << extra_valueptr->getELD() << " "  << extra_coreptr->getName() << extra_coreptr->getNumber() << std::endl;
#endif
					}

					
				} else 
				{
					if(posB != extra_valueptr->getELD())
					{
						idx = extra_valueptr->getNumber();
						test_Value = NULL;
						if(posB < extra_valueptr->getELD())
						{
							test_Value = extra_coreptr->getValue(idx-1);
							if(test_Value)
							{
								temp_data= getELDData(test_Value, extra_valueptr, posB); 
								temp_top = test_Value->getTop() + (posB - test_Value->getELD()) * 100;
							}				
						} else 
						{
							test_Value = extra_coreptr->getValue(idx+1);
							if(test_Value)
							{
								temp_data= getELDData(extra_valueptr, test_Value, posB); 
								temp_top = extra_valueptr->getTop() + (posB - extra_valueptr->getELD()) * 100;
							}				
						}	
						offset = extra_coreptr->getDepthOffset();
						calc_depth = extra_valueptr->calcDepthWithELD(posB);
						test_Value = extra_coreptr->createInterpolatedValue(calc_depth);
						if(test_Value && (test_Value->getMbsf() != calc_depth))
						{
							if(extra_valueptr->getQuality() != GOOD)  continue;

							test_Value->copy(extra_valueptr);
							test_Value->setValueType(INTERPOLATED_VALUE);
							test_Value->setDepth(calc_depth);
							
							test_Value->applyAffine(offset, test_Value->getType());
							
							// need to update data and bottom/top value
							test_Value->setRawData(temp_data);
							test_Value->setTop(temp_top);
							extra_valueptr = test_Value;	
#ifdef DEBUG							
							std::cout << "[DEBUG/sagan] extra value = "  << extra_valueptr->getELD() << " offset" << offset << " " << maincoreptr->getName() << maincoreptr->getNumber() << std::endl;
#endif
						}											
																					
					}

				}
				
//////////////				
				
				
				extra_tieptr = new Tie(SAGAN_TIE);
				extra_tieptr->setId(ret);
				extra_tieptr->setTieTo(logcoreptr, valueA->getType(), valueA->getSection(), rangeA, valueA->getMbsf(), posA);
				extra_tieptr->setTieTo(valueA);
				extra_tieptr->setSharedFlag(true);

				if (extra_valueptr != NULL)
					extra_tieptr->setTied(extra_coreptr, extra_valueptr->getType(), extra_valueptr->getSection(), rangeB, extra_valueptr->getMbsf(), posB);
				else 
					extra_tieptr->setTied(extra_coreptr, valueA->getType(), valueA->getSection(), rangeB, posB, posB);
				extra_tieptr->setTied(extra_valueptr);
				extra_coreptr->addTie(extra_tieptr);		
				addtoSaganTotalTie(extra_tieptr, posA);	
			}
		} 
		addtoSaganTotalTie(tieptr, posA);	
	} else 
	{
		for(iter = m_sagantotalties.begin(); iter != m_sagantotalties.end(); iter++)
		{
			tempTieptr = (Tie*) *iter; 
			if(tempTieptr == NULL) continue;
			
			if(tempTieptr->getId() == tieindex)
			{
				tempTieptr->setTieTo(logcoreptr, valueA->getType(), valueA->getSection(), rangeA, valueA->getMbsf(), posA);
				tempTieptr->setTieTo(valueA);
#ifdef DEBUG				
				cout << "[DEBUG] Update " << tieindex << endl;
#endif
			}
		}					
	}
	
#ifdef DEBUG	
	cout << "[Core-Log Integration] : " << ret << " " << posA << " , " << posB << " : " << holeA << coreidA << ", " << holeB << coreidB << "  --- " <<  valueA->getELD()  << " " << tieptr->getRate() << " " << tieptr->getB() << endl;
#endif	
	//m_logdataptr->update();
	//m_logdataptr->update();
		
	return ret;
}

const char* Correlator::getSaganCoreName(void)
{
	return m_sagan_corename.c_str();
}


void Correlator::addtoSaganTotalTie(Tie* tieptr, double pos)
{
	if(m_saganties.size() == 0)
	{
		m_sagantotalties.push_back(tieptr);
	} else
	{
		std::vector<Tie*>::iterator iter;	
		Tie* tieptrA = NULL;	
		TieInfo* infoTieToA = NULL;
		int success = 0;
		for(iter = m_sagantotalties.begin(); iter != m_sagantotalties.end(); iter++)
		{
			tieptrA = (Tie*) *iter;
			if(tieptrA)
			{
				infoTieToA = tieptrA->getInfoTieTo();
				if(infoTieToA->m_valueptr) 
				{
					if(infoTieToA->m_valueptr->getELD() > pos) 
					{
						m_sagantotalties.insert(iter, tieptr);
						//cout << "where???? -- "  << endl;
						success = 1;
						break;
					}
					
				}
			}
		}
		if(success == 0)
		{
			m_sagantotalties.push_back(tieptr);
		}
	}
}

int Correlator::deleteSagan(int tieid)
{
	//std::cout << "delete sagan ... " << m_sagantotalties.size()  << std::endl;

	Tie* tieptr = NULL;       
	std::vector<Tie*>::iterator iter;   
	Core* coreptr;
	Value* valueptr;
	int index =0;
	iter = m_sagantotalties.begin();
	while(iter != m_sagantotalties.end())
	{
		tieptr = (Tie*) *iter; 
		if(tieptr == NULL) 
		{
			iter++;		
			continue;
		}
		if(tieptr->getId() == tieid)
		{	
#ifdef DEBUG	
			std::cout << tieid << std::endl;
#endif
			m_sagantotalties.erase(iter);
			
			coreptr = tieptr->getTied();
			if (coreptr== NULL) return 0;
			valueptr = tieptr->getTiedValue();
			if(valueptr && valueptr->getValueType() == INTERPOLATED_VALUE)
			{
				tieptr->getTied()->deleteInterpolatedValue(valueptr->getNumber());
			}
			
			valueptr = tieptr->getTieToValue();
			if(valueptr && valueptr->getValueType() == INTERPOLATED_VALUE)
			{
				tieptr->getTieTo()->deleteInterpolatedValue(valueptr->getNumber());
			}			

			coreptr->deleteTie(tieid);
#ifdef DEBUG			
			cout << "[DEBUG] found " << tieid << " erased from m_sagantotalties" << endl;
#endif							
			delete tieptr;
			tieptr = NULL;
		} else 
			iter++;
	}
#ifdef DEBUG	
	cout << "[Core-Log Integration] Undo " << endl;
#endif
	return 1;
}
	

void Correlator::updateTies(void)
{
	Tie* tieptr = NULL;       
	Tie* tieptr_temp = NULL;       
	
	TieInfo* infoTied = NULL;
	std::vector<Tie*>::iterator iter; 
	std::vector<Tie*>::iterator iter_temp;   	
	int tieid_temp; 
	for(iter = m_sagantotalties.begin(); iter != m_sagantotalties.end(); iter++)
	{
		tieptr = (Tie*) *iter; 
		if(tieptr == NULL) continue;
		
		if(tieptr->getSharedFlag() == false)
		{
			infoTied = tieptr->getInfoTied();
			tieid_temp = tieptr->getId();
			tieptr->setTied(infoTied->m_valueptr->getELD());
			
			for(iter_temp = m_sagantotalties.begin(); iter_temp != m_sagantotalties.end(); iter_temp++)
			{
				tieptr_temp = (Tie*) *iter_temp; 
				if(tieptr_temp == NULL) continue;
				if(tieptr == tieptr_temp) continue;
				if(tieid_temp == tieptr_temp->getId())
				{	
					tieptr_temp->setTied(infoTied->m_valueptr->getELD());
#ifdef DEBUG					
					cout << "[DEBUG] Updated --> " << infoTied->m_coreptr->getName() << infoTied->m_coreptr->getNumber() << " " << infoTied->m_mcd << endl;
#endif
				}
			}
		}
	}
}
	
void Correlator::generateSagan(void) 
{
#ifdef DEBUG
	cout << "[DEBUG] Generate Sagan Start" << endl;
#endif	
	Tie* tieptrA = NULL;
	Tie* tieptrB = NULL;

	TieInfo* infoTieToA = NULL;
    TieInfo* infoTiedA = NULL;	
	TieInfo* infoTieToB = NULL;
    TieInfo* infoTiedB = NULL;	

	Value* valueTieToA = NULL;
	Value* valueTiedA = NULL;
	Value* valueTieToB = NULL;
	Value* valueTiedB = NULL;

	double gabA, gabB, gab_offset;
	double a;
	double b, b_back;
	int count = 0;
	int numCores, numTies, numValues;
	Hole* holeptr;
	Core* coreptr;
	Core* first_coreptr = NULL;
	Value* valueptr = NULL;

	int numHoles = m_dataptr->getNumOfHoles();	
	for(int i=0; i < numHoles; i++)
	{
		holeptr = m_dataptr->getHole(i);
		if(holeptr == NULL) continue;
		gab_offset = 999.0f;

		numCores =  holeptr->getNumOfCores();		
		for(int j=0; j <= numCores; j++)
		{
			coreptr = holeptr->getCore(j);
			if(coreptr == NULL) continue;
			numValues = coreptr->getNumOfValues();
			for(int k= 0; k < numValues; k++) 
			{
				valueptr = coreptr->getValue(k);
				if(valueptr == NULL) continue;
				valueptr->resetELD();
			}	
		}		

		if(m_floating == false)
		{
			if(numCores > 0)
			{
				coreptr = holeptr->getCore(0);
				if(coreptr != NULL)
				{
					numValues = coreptr->getNumOfValues();
					if(numValues > 0)
					{
						first_coreptr = coreptr;
						valueTieToA = coreptr->getValue(0);
						valueTiedA = coreptr->getValue(0);
						gab_offset = 0.0f;
						//tieptrB->setB(gab_offset);		
					}
				}
			}
		} else 
		{		
			for(int j=0; j <= numCores; j++)
			{
				coreptr = holeptr->getCore(j);
				if(coreptr == NULL) continue;
						
				numTies = coreptr->getNumOfTies(SAGAN_TIE);
				for(int k=0; k <= numTies; k++)
				{
					tieptrB = coreptr->getTie(SAGAN_TIE, k);
					if(tieptrB == NULL) continue;
					
					infoTieToB = tieptrB->getInfoTieTo();
					infoTiedB = tieptrB->getInfoTied();
					tieptrB->setFirstShiftFlag(true);
													
					gab_offset = infoTieToB->m_valueptr->getELD() - infoTiedB->m_valueptr->getELD();
					tieptrB->setB(gab_offset);
					//std::cout << "first shift flag " << coreptr->getName() << coreptr->getNumber() << " " << gab_offset << std::endl;

					break;
				}
				if(gab_offset != 999.0f)
					break;
			}
		}
		if(gab_offset != 999.0f)
		{
			for(int j=0; j <= numCores; j++)
			{
				coreptr = holeptr->getCore(j);
				if(coreptr == NULL) continue;
				assignShiftToValues(coreptr, gab_offset);
			}			
		}
	}	

	for(int i=0; i < numHoles; i++)
	{
		holeptr = m_dataptr->getHole(i);
		if(holeptr == NULL) continue;
					
		numCores =  holeptr->getNumOfCores();
		count = 0;
		tieptrA = NULL;
		first_coreptr = NULL;
		for(int j=0; j <= numCores; j++)
		{
			coreptr = holeptr->getCore(j);
			if(coreptr == NULL) continue;
			if((first_coreptr == NULL) && (m_floating == false))
			{
				numValues = coreptr->getNumOfValues();
				if(numValues > 0)
				{
					first_coreptr = coreptr;
					valueTieToA = coreptr->getValue(0);
					valueTiedA = coreptr->getValue(0);
				}
			}
			
			numTies = coreptr->getNumOfTies(SAGAN_TIE);
			for(int k=0; k <= numTies; k++)
			{
				tieptrB = coreptr->getTie(SAGAN_TIE, k);
				if(tieptrB == NULL) continue;
				
				
				infoTieToB = tieptrB->getInfoTieTo();
				valueTieToB = infoTieToB->m_valueptr;
				if(valueTieToB == NULL) continue;

				infoTiedB = tieptrB->getInfoTied();
				valueTiedB = infoTiedB->m_valueptr;
				if(valueTiedB == NULL) continue;

				if(count == 0)
					count = 1;
				
				if(tieptrA != NULL)
				{
					if(valueTieToB && valueTieToA && valueTiedB && valueTiedA)
					{
						if(count == 1) 
						{
							tieptrA->setFirstShiftFlag(true);
							count = 2;
						} else {
							tieptrA->setFirstShiftFlag(false);
						}
										
						gabB = valueTieToB->getELD() - valueTieToA->getELD();
						//std::cout << "gabB= " << valueTieToB->getELD() << " , " << valueTieToA->getELD() << std::endl;	
						
						gabA = valueTiedB->getELD() - valueTiedA->getELD();
						//std::cout << "gabA= " << valueTiedB->getELD() << " , " << valueTiedA->getELD() << std::endl;	

						b = valueTieToB->getELD() - valueTiedB->getELD();
												
						a = gabB / gabA;
							
						if (tieptrB && (tieptrB->getStrightFlag() == true))
						{	
							a = 1.0f;
						}
						
						if (tieptrA != NULL)
						{
							tieptrA->setRate(a);
							tieptrA->setB(b);	
						}
						
						assignRateToValues(holeptr, infoTiedA->m_coreptr, infoTiedB->m_coreptr, valueTiedA, valueTiedB, a, b);
						//std::cout << "a= " << a << " b= " << b << std::endl;	
					}	
				} else if(m_floating == false)
				{
					if(valueTieToB && valueTiedB)
					{
						count = 2;
						gabB = valueTieToB->getELD() - valueTiedA->getELD();
						//std::cout << "> gabB= " << valueTieToB->getELD() << " , " << valueTiedA->getELD() << std::endl;	
						
						gabA = valueTiedB->getELD() - valueTiedA->getELD();
						//std::cout << "> gabA= " << valueTiedB->getELD() << " , " << valueTiedA->getELD() << std::endl;	

						b = valueTieToB->getELD() - valueTiedB->getELD();
												
						a = gabB / gabA;
							
						if (tieptrB && (tieptrB->getStrightFlag() == true))
						{	
							a = 1.0f;
						}
						
						assignRateToValues(holeptr, first_coreptr, infoTiedB->m_coreptr, valueTiedA, valueTiedB, a, b);
						//std::cout << "a= " << a << " b= " << b << std::endl;	
					}	
				}
				tieptrA = tieptrB;
				infoTieToA = infoTieToB;
				infoTiedA = infoTiedB;
				valueTieToA = valueTieToB;																		
				valueTiedA = valueTiedB;	

			}
		}
	}

	m_dataptr->update();
	m_dataptr->update();
#ifdef DEBUG	
	cout << "[DEBUG] Generate Sagan End" << endl;
#endif
}

Tie* Correlator::createTie( int type, int coreidA, double relativeposA, int coreidB, double relativeposB )
{
	if(m_dataptr == NULL) return NULL;
	
	// find coreA and coreB
	Core* coreA = findCore(coreidA);
	Core* coreB = findCore(coreidB);	// coreto
	if(coreA == NULL || coreB == NULL) return NULL;

        double posA = (coreA->getBottom() - coreA->getTop()) * relativeposA;
        double posB = (coreB->getBottom() - coreB->getTop()) * relativeposB;

	Tie* pTie = createTie(type, coreA, posA, coreB, posB);
	return pTie;
}

Tie* Correlator::createTie( int type, Core* coreA, double posA, Core* coreB, double posB )
{
	if(m_dataptr == NULL) return NULL;
	if(coreA == NULL || coreB == NULL) return NULL;

	// calculate all inforamtion : top/bottom...
	// top, bottom
	data_range rangeA, rangeB;
	rangeA.top = posA;
	rangeB.top = posB;
	rangeA.bottom = rangeA.top;
	rangeB.bottom = rangeB.top;

	// find value.....
	Value* valueA = findValue(coreA, rangeA.top);
	Value* valueB = findValue(coreB, rangeB.top);
	if(valueA == NULL || valueB == NULL) 
	{
#ifdef DEBUG
		if(type == COMPOSITED_TIE) 
		{
			cout << "[Composite] ";
		} else if(type == REAL_TIE)
		{
			cout << "[Splice] ";
		} else 
		{
			cout << "[Interpolate] ";
		}
		cout << "Error : can not find value" << endl;
#endif
		return NULL; 
	}

	rangeA.top = valueA->getTop();
	rangeA.bottom = rangeA.top;
	rangeB.top = valueB->getTop();
	rangeB.bottom = rangeB.top;
	
	// create Tie and register.......
	Tie* tieptr = new Tie(type);
	if(tieptr == NULL) return NULL;

	if(type == COMPOSITED_TIE) 
	{
		tieptr->setApply(YES);
	}
	//tieptr->setTieTo(coreA, valueA->getType(), valueA->getSection(), rangeA);
	//tieptr->setTied(coreB, valueB->getType(), valueB->getSection(), rangeB);
	tieptr->setTieTo(coreA, valueA->getType(), valueA->getSection(), rangeA, valueA->getMbsf(), posA);
	tieptr->setTied(coreB, valueB->getType(), valueB->getSection(), rangeB, valueB->getMbsf(), posB);

	if(type == COMPOSITED_TIE) 
	{
		coreA->disableTies();
	}
	coreA->addTie(tieptr);
	//coreB->addTie(tieptr);


	m_ties.push_back(tieptr);
	

#ifdef DEBUG
	if(type == COMPOSITED_TIE) 
	{
		cout << "[Composite] ";
	} else if(type == REAL_TIE)
	{
		cout << "[Splice] ";
	} else if(type == SAGAN_TIE)
	{
		cout << "[Core-Log Integration] ";
	} else 
	{
		cout << "[Interpolate] ";
	}
	//cout << "hole " << coreB->getName() << " core " << coreB->getNumber()  << endl;
	cout << coreA->getSite() << " " << coreA->getLeg() << " " << coreA->getName() << " " << coreA->getNumber() << " " << valueA->getType() << " " << valueA->getSection() << " " << rangeA.top  << " " << rangeA.bottom  << " depth" << " tied to ";
	cout << coreB->getSite() << " " << coreB->getLeg() << " " << coreB->getName() << " " << coreB->getNumber() << " " << valueB->getType() << " " << valueB->getSection() << " " << rangeB.top  << " " << rangeB.bottom  << " depth" << endl;

#endif

	return tieptr;
}


Tie* Correlator::createTie( int type, int tieindex, int coreidA, double relativeposA, int coreidB, double relativeposB )
{
	if(m_dataptr == NULL) return NULL;

	Tie* tieptr = NULL;
	Tie* tempTieptr;
	std::vector<Tie*>::iterator iter;
	for(iter = m_ties.begin(); iter != m_ties.end(); iter++)
	{
		tempTieptr = (Tie*) *iter;
		if(tempTieptr->getId() == tieindex)
		{
			tieptr = tempTieptr;
		}
	}
	if(tieptr == NULL) return NULL;
	
	// find coreA and coreB
	Core* coreA = findCore(coreidA);
	Core* coreB = findCore(coreidB);	// coreto
	if(coreA == NULL || coreB == NULL) return NULL;
	
	// calculate all inforamtion : top/bottom...
	// top, bottom
	data_range rangeA, rangeB;
	rangeA.top = (coreA->getBottom() - coreA->getTop()) * relativeposA;
	rangeA.bottom = rangeA.top;
	rangeB.top = (coreB->getBottom() - coreB->getTop()) * relativeposB;
	rangeB.bottom = rangeB.top;
	
	// find value.....
	Value* valueA = findValue(coreA, rangeA.top);
	Value* valueB = findValue(coreB, rangeB.top);
	if(valueA == NULL || valueB == NULL) return NULL;
		
	// create Tie and register.......
	if(tieptr->getTieTo()->getId() == valueB->getId()) 
	{
		tieptr->setTied(coreA, valueA->getType(), valueA->getSection(), rangeA);
		tieptr->setTieTo(coreB, valueB->getType(), valueB->getSection(), rangeB);
	} else 
	{
		tieptr->getTieTo()->deleteTie(tieptr->getId());
		tieptr->setTied(coreA, valueA->getType(), valueA->getSection(), rangeA);
		tieptr->setTieTo(coreB, valueB->getType(), valueB->getSection(), rangeB);
		coreB->addTie(tieptr);
	}
	
#ifdef DEBUG
	if(type == COMPOSITED_TIE) 
	{
		cout << "[Composite] ";
	} else if(type == REAL_TIE)
	{
		cout << "[Splice] ";
	} else 
	{
		cout << "[Interpolate] ";
	}
	cout << "hole " << coreB->getName() << " core " << coreB->getNumber()  << endl;
	cout << coreA->getSite() << " " << coreA->getLeg() << " " << coreA->getName() << " " << coreA->getNumber() << " " << valueA->getType() << " " << valueA->getSection() << " " << rangeA.top  << " " << rangeA.bottom  << " depth" << " toed to ";
	cout << coreB->getSite() << " " << coreB->getLeg() << " " << coreB->getName() << " " << coreB->getNumber() << " " << valueB->getType() << " " << valueB->getSection() << " " << rangeB.top  << " " << rangeB.bottom  << " depth" << endl;

#endif

	return tieptr;
}

Value* Correlator::assignAboveValues( Core* coreptr, Core* source, Value* valueptr, bool isConstrained, double tie_depth, double offset)
{
	//int index = coreptr->getNumOfValues();
	if(valueptr == NULL) return NULL;
	int index = 0;

	int size = source->getNumOfValues();
	Value* newValue = NULL;
	Value* lastvalue = NULL;
	Value* sourceValue = NULL;
	int i=0;
	double depth;
	
	for(i=0 ; i < size; i++, index++) 
	{
		newValue = coreptr->createValue(index); 
		if(newValue == NULL) continue;
		sourceValue = source->getValue(i);
		if(sourceValue == NULL) continue;
		if(source->getQuality() != GOOD)  continue;

		newValue->copy(source->getValue(i));
		newValue->setSource(source->getValue(i));
		
		newValue->setB(offset);		
		//newValue->setMcd(sourceValue->getSpliceMcd() + offset);
		//newValue->setELD(sourceValue->getELD() + offset);
			
		if(source->getValue(i)->getId()  == valueptr->getId()) 
		{
			//std::cout << "above " << valueptr->getMcd() << std::endl;
			break;
		}
	} 	
	
	return newValue;
}

Value* Correlator::assignBetweenValues( Core* source, Value* valueptr, double gap )
{
	//std::cout << "------------ assign between value 2 " << std::endl;
	// HEEEEEE
	int size = source->getNumOfValues();
	if(valueptr == NULL) return NULL;

	double depth = valueptr->getELD() + gap; 

	for(int i=valueptr->getNumber() ; i < size; i++) 
	{
		if(source->getValue(i)->getELD() > depth)
		{
			return source->getValue(i);
		}
	} 
	return NULL;
}

Value* Correlator::assignBetweenValues( Core* coreptr, Core* source, Value* valueptrA, Value* valueptrB, Value* lastvalue, bool isConstrained, double tie_depth, double offset)
{
	int size = source->getNumOfValues();
	if(valueptrA == NULL  || valueptrB == NULL) return NULL;

	Value* newValue = NULL;
	int i;
	i = valueptrA->getNumber();
	if(i == size) return NULL;
	//int start = i+1;
	int start = i;
#ifdef DEBUG	
	if(valueptrA->getValueType() == INTERPOLATED_VALUE)
		cout << "[DEBUG] interpolated value " << valueptrA->getMcd() << endl;
#endif
	
	if(isConstrained == false)
	{
		valueptrB = findValue(source, valueptrB->getELD() - offset);
		//valueptrB = findValueWithMcd(source, valueptrB->getMcd() - offset);
#ifdef DEBUG
		std::cout << "[DEBUG] constrained ??? " << std::endl;
#endif
		if(valueptrB == NULL) return NULL;
		lastvalue = NULL;
	}
			
	i = valueptrB->getNumber() ;
	if(i == size) return NULL;
	int end = i+1;
	if(end > size) end = size;	 
	
	Value* sourceValue = NULL;
	Value* source_last_Value = NULL;
	int index =0;
	double depth;
	if(lastvalue != NULL)
	{
		
		depth = lastvalue->getMcd() - source->getDepthOffset();
		newValue = coreptr->createValue(index); 
		sourceValue = source->getValue(start);
		if(sourceValue->getQuality() == GOOD)  
		{
			newValue->copy(sourceValue);
			newValue->setSource(sourceValue);
		
			newValue->setDepth(depth);
			newValue->applyAffine(source->getDepthOffset(), newValue->getType());
			newValue->setRawData(lastvalue->getRawData());
			newValue->setB(offset);
			index++;
		}				
	}
	
	//std::cout << start << " " << end  << " " << size  << " : " << valueptrA->getMcd() << " " << valueptrB->getMcd () << std::endl;
	sourceValue = NULL;
	for(i= start; i < end; i++, index++) 
	{
		newValue = coreptr->createValue(index); 
		if(newValue == NULL) continue;
		
		sourceValue = source->getValue(i);
		if(sourceValue == NULL) continue;
		if(source->getQuality() != GOOD)  continue;


		newValue->copy(source->getValue(i));
		newValue->setSource(source->getValue(i));
				
		newValue->setB(offset);	
		newValue->setMcd(sourceValue->getSpliceMcd() + offset);
		newValue->setELD(sourceValue->getELD() + offset);
		
		//cout << source->getName() << source->getNumber() << " " << i << " " << newValue->getMcd() << " " <<  sourceValue->getRawData() <<  " " << sourceValue->getData() << endl;		
			
		//cout << " add between " << sourceValue->getELD() << " " <<  offset << endl;
		//cout << source->getName() << source->getNumber() << "TEST MCD : " << sourceValue->getMcd() << " ELD : " << sourceValue->getELD() << endl;
		//cout << "MCD : " << newValue->getMcd() << " ELD : " << newValue->getELD() << endl;
	}

	//cout << "coreptr value size " << coreptr->getNumOfValues() << endl;
	return newValue;
}

Value* Correlator::assignBelowValues( Core* coreptr, Core* source, Value* valueptr, Value* lastvalue, bool isConstrained, double tie_depth, double offset)
{
	//int index = coreptr->getNumOfValues();
	//std::cout << "assignBelowValues offset = " << offset << std::endl;

 	int size = source->getNumOfValues();
	Value* newValue = NULL;
	int i;
	for(i=0 ; i < size; i++) 
	{
		if(source->getValue(i)->getId()  == valueptr->getId())
		{
			//std::cout << "below " << valueptr->getMcd() << std::endl;
			break;
		}
	} 
	//i++;  //--- just now

	if(i == size) return NULL;	 

	if(isConstrained == false)
	{
		lastvalue = NULL;
	}
	
	int index =0;
	Value* sourceValue = NULL;
	Value* source_last_Value = NULL;
	if(lastvalue != NULL)
	{
		double depth = lastvalue->getMcd() - source->getDepthOffset();
		newValue = coreptr->createValue(index); 
		sourceValue = source->getValue(i);
		if(sourceValue->getQuality() == GOOD)  
		{

			newValue->copy(sourceValue);
			newValue->setSource(sourceValue);
			
			newValue->setDepth(depth);
			newValue->applyAffine(source->getDepthOffset(), newValue->getType());
			newValue->setRawData(lastvalue->getRawData());
			index++;
		}				
		//cout << "(below) last " << newValue->getMcd() << " " << newValue->getData() << endl;
	}

	
	for(; i < size; i++, index++) 
	{
		newValue = coreptr->createValue(index); 
		if(source->getQuality() != GOOD)  continue;
		
		newValue->copy(source->getValue(i));
		newValue->setSource(source->getValue(i));
		
		newValue->setB(offset);
		newValue->setMcd(newValue->getSpliceMcd() + offset);
		newValue->setELD(newValue->getELD() + offset);	
	}

	return newValue;
}

int Correlator::assignShiftToValues(Core* coreptr, double offset)
{
	double modified_offset;	
	if(coreptr)
	{
		//modified_offset = coreptr->getDepthOffset() +offset;
		//coreptr->setDepthOffset(modified_offset, true);

		Value* newValue = NULL;
		int end = coreptr->getNumOfValues();
		for(int i= 0; i < end; i++) 
		{
			newValue = coreptr->getValue(i);
			newValue->setB(offset);
		}	

	
	}

	return 1;
}

int Correlator::assignShiftToValues(double offset)
{
	Tie* tieptr = NULL;
	TieInfo* infoTied = NULL;
	TieInfo* infoTieTo = NULL;

	Core* coreTieTo = NULL;
	std::vector<Tie*>::iterator iter;
	int size =0;
	int end = 0;
	Value* newValue = NULL;
	
	data_range rangeA, rangeB;
	double modified_offset;
	if(m_splicerties.size() > 0)
	{
		iter = m_splicerties.begin();
		tieptr = (Tie*) *iter;
		infoTied = tieptr->getInfoTied();	
		if(infoTied)
		{
			coreTieTo = infoTied->m_coreptr;
			if(coreTieTo)
			{
				//cout << " coreTieTo : " << coreTieTo->getName() << coreTieTo->getNumber() << endl;
				end = coreTieTo->getNumOfValues();
				for(int i= 0; i < end; i++) 
				{
					newValue = coreTieTo->getValue(i);
					newValue->resetELD();
					newValue->setB(offset);
				}				
			}			
		}
	}
	
	for(iter = m_splicerties.begin(); iter != m_splicerties.end(); iter++)
	{
		tieptr = (Tie*) *iter;
		infoTieTo = tieptr->getInfoTieTo();
		if(infoTieTo)
		{
			coreTieTo = infoTieTo->m_coreptr;
			if(coreTieTo)
			{
				//cout << " coreTieTo : " << coreTieTo->getName() << coreTieTo->getNumber() << endl;
				end = coreTieTo->getNumOfValues();
				for(int i= 0; i < end; i++) 
				{
					newValue = coreTieTo->getValue(i);
					newValue->resetELD();
					newValue->setB(offset);
				}				
			}
		}
	}

	return 1;
}

int Correlator::assignRateToValues(Hole* holeptr, Core* coreptrA, Core* coreptrB, Value* valueptrA, Value* valueptrB, double rate, double b)
{

	if(coreptrA == NULL || coreptrB == NULL) return 0;
	if(valueptrA == NULL  || valueptrB == NULL) return 0;
	
	int valueA_id = valueptrA->getId();
	int valueB_id = valueptrB->getId();
		
 	int size = coreptrA->getNumOfValues();
	int i;
	for(i=0; i < size; i++) 
	{
		if(coreptrA->getValue(i) != NULL)
		{
			if(coreptrA->getValue(i)->getId() == valueA_id)
			{
				i++;
				break;
			}
		}
	} 
	int start = i;
	if(i == size) start = -1;	 
	
	int end = size;
	int flag = 0;
	// if tie is in the same core, 
	if(coreptrA->getNumber() == coreptrB->getNumber())
	{
		flag = 1;
	} else 
	{
		i = 0;
		size = coreptrB->getNumOfValues();
	}
	for(; i < size; i++) 
	{	
		if(coreptrB->getValue(i) != NULL)
		{
			if(coreptrB->getValue(i)->getId() == valueB_id)
			{
				end = i;
				break;
			}
		}
	}	
	//cout << "start, end : " << start << " " << end << endl;

	Value* newValue = NULL;
	double offset = b;

	int numCores =  holeptr->getNumOfCores();
	int coreA_id = coreptrA->getNumber();
	int coreB_id = coreptrB->getNumber();
	Core* coreptr = NULL;
	
	if(flag == 1)
	{
		for(i=start; i <= end; i++) 
		{
			newValue = coreptrA->getValue(i);
			if(newValue == NULL) continue;
			
			newValue->setStretch(rate, valueptrA->getELD());
		}
		end++;
		for(i=end; i < size; i++)
		{
			newValue = coreptrA->getValue(i);
			if(newValue == NULL) continue;
			newValue->setB(offset);
		}	
		
		for(int k=0; k <= numCores; k++)
		{
			coreptr = holeptr->getCore(k);
			if(coreptr == NULL) continue;
			
			if(coreptr->getNumber() == coreB_id)
			{
				coreB_id = k+1;
				break;
			} 
		}
				
	} else 
	{
		size = coreptrA->getNumOfValues();
		if (start >= 0)
		{
			for(i=start; i < size; i++) 
			{
				newValue = coreptrA->getValue(i);
				if(newValue == NULL) continue;
				newValue->setStretch(rate, valueptrA->getELD());
			}
		}
		
		bool start_flag = false;
		for(int k=0; k <= numCores; k++)
		{
			coreptr = holeptr->getCore(k);
			if(coreptr == NULL) continue;
			
			if(start_flag == false)
			{
				if(coreptr->getNumber() == coreA_id)
					start_flag = true;
			} else 
			{
				if(coreptr->getNumber() == coreB_id)
				{
					coreB_id = k+1;
					break;
				} else 
				{
					size = coreptr->getNumOfValues();
					for(i=0; i < size; i++) 
					{
						newValue = coreptr->getValue(i);
						if(newValue == NULL) continue;
						newValue->setStretch(rate, valueptrA->getELD());
					}
				}
			}
		}
		for(i=0; i <= end; i++) 
		{
			newValue = coreptrB->getValue(i);
			if(newValue == NULL) continue;
			
			newValue->setStretch(rate, valueptrA->getELD());
		}		
		size = coreptrB->getNumOfValues();

		end++;
		for(i=end; i < size; i++)
		{
			newValue = coreptrB->getValue(i);
			if(newValue == NULL) continue;
			newValue->setB(offset);
		}
			
	}
	
	for(int k=coreB_id; k <= numCores; k++)
	{
		coreptr = holeptr->getCore(k);
		if(coreptr == NULL) continue;

		size = coreptr->getNumOfValues();
		for(i=0; i < size; i++) 
		{
			newValue = coreptr->getValue(i);
			if(newValue == NULL) continue;
			newValue->setB(offset);
		}
	}

	return 1;
}


void Correlator::createSpliceHole( void )
{
	/*if(m_depthstep <= 0.0f)
	{
		return 0;
	}
	if(m_winlen <= 0.0f || m_leadlagmeters <= 0.0f)
	{
		return 0;
	} */
	
	// create Hole
	int index = m_splicerholes.size();
	Hole* newHole = new Hole(index, NULL);
	m_mainHole[0] = newHole;
	m_mainHole[0]->setName("X");
	m_mainHole[0]->setParent(&m_correlatorData);
	// setName .......
	
	m_splicerholes.push_back(newHole);
}

int Correlator::deleteTie( int tieindex )
{
	Tie* tieptr = NULL;
	Tie* tempTieptr;
	std::vector<Tie*>::iterator iter;
	for(iter = m_ties.begin(); iter != m_ties.end(); iter++)
	{
		tempTieptr = (Tie*) *iter;
		if(tempTieptr->getId() == tieindex)
		{
			tieptr = tempTieptr;
		}
	}
	if(tieptr == NULL) return -1;
	
	tieptr->getTieTo()->deleteTie(tieptr->getId());
	delete tieptr;
	tieptr = NULL;
	m_ties.erase(iter);
	
	// todo
	// if splice...

	return 1;
}
	
double Correlator::repickDepth( int coreid, double relativepos )
{
	// find coreA and coreB
	Core* coreptr = findCore(coreid);
	if(coreptr == NULL) return 0.0;
	
	// calculate all inforamtion : top/bottom...
	// top, bottom
	double top;
	top = (coreptr->getBottom() - coreptr->getTop()) * relativepos;
	
	// find value.....
	Value* valueptr = findValue(coreptr, top);
	if(valueptr == NULL) return 0.0;
	
	return valueptr->getELD();
	// todo : interpolate.......
}

int Correlator::evalCoreLog(char* holeA, int coreidA, double posA, double posB)
{
	Core* logcoreptr = NULL;
	if(m_logdataptr)
	{
		Hole* log_hole = m_logdataptr->getHole(0);
		if(log_hole)
		{
			logcoreptr = log_hole->getCore(0);
		}

		if(logcoreptr == NULL) return 0;

		if(logcoreptr->getMinDepth() > posB) return 0;
		
	} else 
		return 0;	
			
	//Core* coreptrA = findCore(holeA, coreidA);

	Value* valueB = NULL;
	if ((m_mainHole[0] == NULL) && (m_mainHole[1] == NULL)) {
		Core* temp_core = findCore(holeA, coreidA);
		valueB = findValueInHole((Hole*)temp_core->getParent(), posB);		
	} else 
	{
		if(m_mainHole[1] == NULL)
			valueB = findValueInHole(m_mainHole[0], posB);
		else 
			valueB = findValueInHole(m_mainHole[1], posB);
	}
		
	if(valueB == NULL)
		return 0;
		
	Core* coreptrA = (Core*) valueB->getParent();
		
	if(coreptrA == NULL)
	{
#ifdef DEBUG
			cout << "[evalCoreLog] Error : can not find core" << endl;
#endif
			return  0;
	}
	//cout << "hole : " << holeA << " " << coreidA << " " <<  posA << " " <<  posB << endl;
	
	return evalCore(coreptrA, posA, logcoreptr, posB);
}


int Correlator::evalSpliceCore(int coretypeB, char* annotB, char* holeB, int coreidB, double posB, double posA)
{
	if(m_dataptr == NULL) return 0;
	if(m_mainHole[0] == NULL) return 0;

	Value* valueptr = findValueInHole(m_mainHole[0], posA);
	if(valueptr == NULL) 
	{
		//cout << "[Eval Graph] Error : can not find value" << endl;
		return 0;
	}
	Core* coreptrA = (Core*)valueptr->getParent();
	if(coreptrA == NULL)
	{
#ifdef DEBUG
		//cout << "[Eval Graph] Error : can not find core" << endl;
#endif
		return  0;
	}
	
	//Core* coreptrA = findCore(coretypeA, holeA, coreidA, annotA);
	Core* coreptrB = findCore(coretypeB, holeB, coreidB, annotB);
	//cout << coretypeA << "--------- start" << endl;
	if(coreptrB == NULL)
	{
#ifdef DEBUG
		//cout << "[Eval Graph] Error : can not find core" << endl;
#endif
		return  0;
	}
	return evalCore(coreptrA, posA, coreptrB, posB);
	
}
	
	
int Correlator::evalCore(int coretypeA, char* annotA, char* holeA, int coreidA, double posA, int coretypeB, char* annotB, char* holeB, int coreidB, double posB)
{
	if(m_dataptr == NULL) return 0;

	Core* coreptrA = findCore(coretypeA, holeA, coreidA, annotA);
	Core* coreptrB = findCore(coretypeA, holeB, coreidB, annotB);
	//cout << coretypeA << "--------- start" << endl;
	
	if(coreptrA == NULL || coreptrB == NULL)
	{
#ifdef DEBUG
		//cout << "[Eval Graph] Error : can not find core" << endl;
#endif
		return  0;
	}
	return evalCore(coreptrA, posA, coreptrB, posB);
	
}
	
double Correlator::getData(Value* prev_valueptr, Value* next_valueptr, double depth)
{
	//double diff_depth = next_valueptr->getELD() - prev_valueptr->getELD();
	double diff_depth = next_valueptr->getMcd() - prev_valueptr->getMcd();
	//std::cout << "diff depth = " << diff_depth << std::endl;
		
	double diff_data = next_valueptr->getData() - prev_valueptr->getData();
	//std::cout << "diff data = " << diff_data << std::endl;

	if (diff_data == 0)
		return next_valueptr->getData();
	if (diff_depth == 0)
		return next_valueptr->getData();
				
	double a = diff_depth / diff_data;
	//double b = next_valueptr->getELD() - a * next_valueptr->getData();
	double b = next_valueptr->getMcd() - a * next_valueptr->getData();
	
	//std::cout << a << ", " << b << std::endl;
	
	double ret = (depth - b) / a;
	return ret;
}

double Correlator::getELDData(Value* prev_valueptr, Value* next_valueptr, double depth)
{
	//double diff_depth = next_valueptr->getELD() - prev_valueptr->getELD();
	double diff_depth = next_valueptr->getELD() - prev_valueptr->getELD();
	//std::cout << "diff depth = " << diff_depth << std::endl;
		
	double diff_data = next_valueptr->getData() - prev_valueptr->getData();
	//std::cout << "diff data = " << diff_data << std::endl;

	if (diff_data == 0)
		return next_valueptr->getData();
	if (diff_depth == 0)
		return next_valueptr->getData();
				
	double a = diff_depth / diff_data;
	//double b = next_valueptr->getELD() - a * next_valueptr->getData();
	double b = next_valueptr->getELD() - a * next_valueptr->getData();
	
	//std::cout << a << ", " << b << std::endl;
	
	double ret = (depth - b) / a;
	return ret;
}

double Correlator::getMbsfData(Value* prev_valueptr, Value* next_valueptr, double depth)
{
	//double diff_depth = next_valueptr->getELD() - prev_valueptr->getELD();
	double diff_depth = next_valueptr->getMbsf() - prev_valueptr->getMbsf();
	//std::cout << "diff depth = " << diff_depth << std::endl;
		
	double diff_data = next_valueptr->getData() - prev_valueptr->getData();
	//std::cout << "diff data = " << diff_data << std::endl;

	if (diff_data == 0)
		return next_valueptr->getData();
	if (diff_depth == 0)
		return next_valueptr->getData();
				
	double a = diff_depth / diff_data;
	//double b = next_valueptr->getELD() - a * next_valueptr->getData();
	double b = next_valueptr->getMbsf() - a * next_valueptr->getData();
	
	//std::cout << a << ", " << b << std::endl;
	
	double ret = (depth - b) / a;
	return ret;
}

double Correlator::getTop(Value* prev_valueptr, Value* next_valueptr, double depth)
{
	//double diff_depth = next_valueptr->getELD() - prev_valueptr->getELD();
	double diff_depth = next_valueptr->getMcd() - prev_valueptr->getMcd();

	double diff_data = next_valueptr->getTop() - prev_valueptr->getTop();
	
	if (diff_data == 0)
		return next_valueptr->getTop();
		
	double a = diff_depth / diff_data;
	//double b = next_valueptr->getELD() - a * next_valueptr->getData();
	double b = next_valueptr->getMcd() - a * next_valueptr->getTop();
	
	double ret = (depth - b) / a;
	return ret;
}


int Correlator::evalCore(Core* coreptrA, double posA, Core* coreptrB, double posB)
{	
	// find value.....
	Value* valueA = findValue(coreptrA, posA);
	if(valueA == NULL)
	{
#ifdef DEBUG
		cout << "[Eval Graph] Error : can not find value A " << posA << endl;
#endif
		return 0;
	}

	Value* valueB = findValue(coreptrB, posB);
	if(valueB == NULL)
	{
#ifdef DEBUG
		cout << "[Eval Graph] Error : can not find value B " << posB << endl;
#endif
		return 0;
	}
	int size_B = coreptrB->getNumOfValues() -1;
	
	int idx_B;
	Value* temp_valueB = NULL;
	double temp_data;
	if(posB < valueB->getELD())
	{
		idx_B = valueB->getNumber() -1;
		if(idx_B > 0)
		{
			temp_valueB = coreptrB->getValue(idx_B);
			temp_data= getData(temp_valueB, valueB, posB);
			//cout << "(" << temp_valueB->getELD() << "," << temp_valueB->getData() << ") (" <<   valueB->getELD() << "," << valueB->getData() << ") to--> (" << posB  << "," << temp_data << ")" << endl;
		}
	} else 
	{
		idx_B = valueB->getNumber() + 1;
		if(idx_B < size_B)
		{
			temp_valueB = coreptrB->getValue(idx_B);
			temp_data= getData(valueB, temp_valueB, posB);
			//cout << "(" << valueB->getELD() << "," << valueB->getData() << ") (" <<   temp_valueB->getELD() << "," << temp_valueB->getData() << ") to--> (" << posB  << "," << temp_data << ")" << endl;
		}
	}
	double leadlag = m_leadlagmeters/m_depthstep;
	int numlags = int(leadlag) *2 +1; 
	
	double eval = 0;
	double startdepth = posB - m_leadlagmeters;
	double fixedstartdepth = posA;
	double gab_value=0.0;
	Value* valueptrA = findValue(coreptrA, fixedstartdepth-m_winlen);
	if(valueptrA == NULL)
	{
		valueptrA = coreptrA->getValue(0);
		gab_value = valueptrA->getELD() - fixedstartdepth + m_winlen;
		//cout << "[DEBUG] Start gab = " << gab_value <<  " (" << fixedstartdepth - m_winlen  << ", " << valueptrA->getELD() << ")" << endl;
	}
	if (valueptrA == NULL) return 0;

	m_coeflist.clear();

	Value* valueptrB = NULL;
	Value* valueptrTempA = valueptrA;
	Value* valueptrTempB = NULL;

	double gab =0;
	double exp_depth;
	double depth;
	for(int i =0; i < numlags; i++)
	{
		exp_depth = startdepth - m_winlen;
		eval = evalCore(coreptrA, valueptrA, fixedstartdepth, coreptrB, startdepth, numlags, gab_value);

		depth  = startdepth - posB;
		m_coeflist.push_back(depth);
		m_coeflist.push_back(eval);

		startdepth += m_depthstep;
	}

	return 1;
}

double Correlator::evalCore(Core* fixedCore, Value* fixedValue, double fixedStart, Core* coreptr, double startdepth, int numlags, double gab)
{
	double depth;
	int idx;
	Value* temp_valueptr=NULL;
	double temp_data;
	int fixedSize  = fixedCore->getNumOfValues() -1;
	int movableSize  = coreptr->getNumOfValues() -1;
	Value* valueptr = NULL;

	///////////////////////////////
	// calculate coef
	double sumX = 0.0, sumY = 0.0;
	double sumXsq = 0.0, sumYsq = 0.0;
	double sumXYsq = 0.0;

	int nx = 0;
	double valueX=0.0, depthX=0.0, valueY =0.0, depthY=0.0;
	double gabX=0.0, gabY=0.0;
	double prevdepthX=0.0f, prevdepthY=0.0f;
	double gap = 0.0f;

	fixedStart += gab;
	startdepth += gab;
	
	for(int i=0; i < numlags; i++)
	{
		depth = fixedStart - m_winlen;
		if(fixedValue == NULL)
			fixedValue = findValue(fixedCore, depth);
		else 
			fixedValue = findValue(fixedCore, depth, fixedValue->getNumber());

		if(fixedValue == NULL) 
		{
			fixedStart += m_depthstep;
			startdepth += m_depthstep;
			continue;		
		}
		if(depth < fixedValue->getELD())
		{
			idx = fixedValue->getNumber() -1;
			if(idx > 0)
			{
				temp_valueptr = fixedCore->getValue(idx);
				temp_data= getData(temp_valueptr, fixedValue, depth);
				//cout << "(" << temp_valueptr->getELD() << "," << temp_valueptr->getData() << ") (" <<  fixedValue->getELD() << "," << fixedValue->getData() << ") to--> (" << depth  << "," << temp_data << ")" << endl;
			} else 
				continue;
		} else 
		{
			idx = fixedValue->getNumber() + 1;
			if(idx < fixedSize)
			{
				temp_valueptr = fixedCore->getValue(idx);
				temp_data= getData(fixedValue, temp_valueptr, depth);
				//cout << "(" << fixedValue->getELD() << "," << fixedValue->getData() << ") (" <<   temp_valueptr->getELD() << "," << temp_valueptr->getData() << ") to--> (" << depth  << "," << temp_data << ")" << endl;
			} else 
				break;
		}
		if(temp_data == -999.0)
		{
			fixedStart += m_depthstep;
			startdepth += m_depthstep;
			continue;		
		}
		fixedStart += m_depthstep;		
		valueX = temp_data; 
		depthX = depth;
		
		depth = startdepth - m_winlen;
		if(valueptr == NULL)
			valueptr = findValue(coreptr, depth);
		else 
			valueptr = findValue(coreptr, depth, valueptr->getNumber());
		if(valueptr == NULL) 
		{
			startdepth += m_depthstep;
			continue;		
		}				
		if(depth < valueptr->getELD())
		{
			idx = valueptr->getNumber() -1;
			if(idx > 0)
			{
				temp_valueptr = coreptr->getValue(idx);
				temp_data= getData(temp_valueptr, valueptr, depth);
				//cout << "(" << temp_valueptr->getELD() << "," << temp_valueptr->getData() << ") (" <<  valueptr->getELD() << "," << valueptr->getData() << ") to--> (" << depth  << "," << temp_data << ")" << endl;
			} else 
				continue;
		} else 
		{
			idx = valueptr->getNumber() + 1;
			if(idx < movableSize)
			{
				temp_valueptr = coreptr->getValue(idx);
				temp_data= getData(valueptr, temp_valueptr, depth);
				//cout << "(" << valueptr->getELD() << "," << valueptr->getData() << ") (" <<   temp_valueptr->getELD() << "," << temp_valueptr->getData() << ") to--> (" << depth  << "," << temp_data << ")" << endl;
			} else 
				break;
		}			
		if(temp_data == -999.0) 
		{
			startdepth += m_depthstep;
			continue;		
		}				
		startdepth += m_depthstep;			
		valueY = temp_data; 
		depthY = depth;
		//cout << "(" << depthX << ", " << valueX << ") (" << depthY << ", " << valueY << ")" << endl;
		
		gabX = round((depthX - prevdepthX) / m_depthstep);
		gabY = round((depthY - prevdepthY) / m_depthstep);
		prevdepthX = depthX;
		prevdepthY = depthY;
		
		sumX = sumX + valueX;
		sumXsq = sumXsq + (valueX * valueX);
		sumY = sumY + valueY;
		sumYsq = sumYsq + (valueY * valueY);
		sumXYsq =  sumXYsq + (valueX * valueY);
		nx++;
	}
	
	// calculate the standard deviation and the correlation coeficiant
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
			coef = ((nx * sumXYsq) - (sumX * sumY)) / (stdevX * stdevY);
		}
	} else
	{
		coef=0.0;
	}

	return coef;	
}


double Correlator::evalCore( Core* coreA, Core* coreB, Value* valueA, Value* valueB, double endpoint, Value* valueEndA )
{
	///////////////////////////////
	// find start and end
	int n = coreA->getNumOfValues() -1;
	if(valueEndA) n = valueEndA->getNumber();
	
	int nY = coreB->getNumOfValues() -1;
	Value* valueptr = findValue(coreB, endpoint);
	if(valueptr != NULL)  nY = valueptr->getNumber();
	
	int a = valueA->getNumber();
	int b = valueB->getNumber();	
	int end = n -a; 	
	if (end > (nY-b))
	{
		end = nY-b;
	}

	///////////////////////////////
	// calculate coef
	double sumX = 0.0;
	double sumXsq = 0.0;
	double sumY = 0.0;
	double sumYsq = 0.0;
	double sumXYsq = 0.0;

	int nx = 0;
	double valueX, valueY;
	Value* valueptrA = NULL;
	Value* valueptrB = NULL;
	a--;
	b--;
	double gabX, gabY, prevdepthX=0.0f, prevdepthY=0.0f, depthX, depthY;
	double gap = 0.0f;
	// m_depthstep
	Value* prevValueptrA = NULL;
	Value* prevValueptrB = NULL;
	
	for(int i = 0; i <= end; i++)
	{
		a ++;	
		if (a >  n) break;
		valueptrA = coreA->getValue(a);
		if(valueptrA == NULL) continue;
		if(prevValueptrA != NULL)
		{
			gap = valueptrA->getELD() - prevValueptrA->getELD();
			if(m_depthstep > gap)
			{
				b++;
				continue;
			}
		}
		valueX = valueptrA->getData(); 
		depthX = valueptrA->getELD();
		prevValueptrA = valueptrA;
		
		b ++;	
		if (b >  nY) break;
		valueptrB = coreB->getValue(b);
		if(valueptrB == NULL) continue;
		if(prevValueptrB != NULL)
		{
			gap = valueptrB->getELD() - prevValueptrB->getELD();
			while(m_depthstep > gap)
			{
				b++;
				if (b >  nY) break;
				valueptrB = coreB->getValue(b);
				if(valueptrB == NULL) continue;
				gap = valueptrB->getELD() - prevValueptrB->getELD();
			}
			if (b >  nY) break;
		}

		valueY = valueptrB->getData(); 
		depthY = valueptrB->getELD();
		prevValueptrB = valueptrB;
		
		gabX = round((depthX - prevdepthX) / m_depthstep);
		gabY = round((depthY - prevdepthY) / m_depthstep);
		prevdepthX = depthX;
		prevdepthY = depthY;
		// HYEJUNG NO REASON
		//if((gabX > 1) || (gabY > 1)) continue; 
		if(valueptrA->getQuality() != BAD_PT || valueptrB->getQuality() != BAD_PT)
		{
			sumX = sumX + valueX;
			sumXsq = sumXsq + (valueX * valueX);
			sumY = sumY + valueY;
			sumYsq = sumYsq + (valueY * valueY);
			sumXYsq =  sumXYsq + (valueX * valueY);
			nx++;
		}
		
	}


	// calculate the standard deviation and the correlation coeficiant
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
			coef = ((nx * sumXYsq) - (sumX * sumY)) / (stdevX * stdevY);
		}
	} else
	{
		coef=0.0;
	}

	return coef;
}


Core* Correlator::findCore( int index )
{
	 if(m_dataptr == NULL) return NULL;

	int numHoles = m_dataptr->getNumOfHoles();
	int numCores;
	
	Hole* holeptr;
	Core* coreptr;
	for(int i=0; i < numHoles; i++)
	{
		 holeptr = m_dataptr->getHole(i);
		 if(holeptr == NULL) continue;
		 numCores =  holeptr->getNumOfCores();
		 for(int j=0; j < numCores; j++)
		 {
			coreptr = holeptr->getCore(j);
			if(coreptr == NULL) continue;
			if(coreptr->getId() == index)
			{
				return coreptr;
			}
		 }
	}
	return NULL;
}

Core* Correlator::findCore( char* holeName, int coreId, int index )
{
	int numHoles = m_dataptr->getNumOfHoles();
	int numCores;
	
	Hole* holeptr;
	Core* coreptr;
	int count = 0;	
	char* hole_ptr;			
	for(int i=0; i < numHoles; i++)
	{
		holeptr = m_dataptr->getHole(i);
		hole_ptr = (char*) holeptr->getName();
		if(strcmp(hole_ptr, holeName) == 0) 
		{
			if(index == count)
			{
				numCores =  holeptr->getNumOfCores();
				for(int j=0; j <= numCores; j++)
				{
					coreptr = holeptr->getCore(j);
					if(coreptr == NULL) continue;
					
					if(coreptr->getNumber() == coreId)
					{
						return coreptr;
					}
				}
			}
			count++;
		}
	}
	
	return NULL;
}

Core* Correlator::findCore( int type, const char* holeName, int coreId, const char* annot, int index )
{
	int numHoles = m_dataptr->getNumOfHoles();
	int numCores;
	if((type == USERDEFINEDTYPE) && (annot == NULL)) return NULL;
	
	
	Hole* holeptr;
	Core* coreptr;
	int count = 0;	
	char* hole_ptr;			
	for(int i=0; i < numHoles; i++)
	{
		holeptr = m_dataptr->getHole(i);
		//if((holeptr->getName() == holeName) && (holeptr->getType() == type))
		hole_ptr = (char*) holeptr->getName();
		if(strcmp(hole_ptr, holeName) == 0) 
		{
			if(type == USERDEFINEDTYPE)
			{
				if(strcmp(holeptr->getAnnotation(), annot) == 0)
				{
					if(index == count)
					{
						numCores =  holeptr->getNumOfCores();
						for(int j=0; j <= numCores; j++)
						{
							coreptr = holeptr->getCore(j);
							if(coreptr == NULL) continue;
							
							if(coreptr->getNumber() == coreId)
							{
								return coreptr;
							}
						}
					}
					count++;
				}
			} else if(holeptr->getType() == type)
			{
				if(index == count)
				{
					numCores =  holeptr->getNumOfCores();
					for(int j=0; j <= numCores; j++)
					{
						coreptr = holeptr->getCore(j);
						if(coreptr == NULL) continue;
						
						if(coreptr->getNumber() == coreId)
						{
							return coreptr;
						}
					}
				}
				count++;
			}
		}
	}
	
	return NULL;
}
		

Core* Correlator::findCoreinSplice( int index )
{
	if(m_mainHole[0] == NULL) return NULL;
	
	Core* coreptr;
	int numCores =  m_mainHole[0]->getNumOfCores();
	for(int i=0; i < numCores; i++)
	{
		coreptr = m_mainHole[0]->getCore(i);
		if(coreptr == NULL) continue;
		if(coreptr->getId() == index)
		{
			return coreptr;
		}
	}
	return NULL;
}	
	

Tie* Correlator::findTie( int order, bool alternative )
{
	if (m_dataptr == NULL) return NULL;
	
    int numHoles = m_dataptr->getNumOfHoles();
    int numCores, numTies;
	int tie_type = REAL_TIE;
	if (alternative == true)
		tie_type = ALT_REAL_TIE;

    Hole* holeptr;
    Core* coreptr;
    Tie* tieptr;
    for(int i=0; i < numHoles; i++)
    {
		holeptr = m_dataptr->getHole(i);
        if(holeptr == NULL) continue;
		
        numCores =  holeptr->getNumOfCores();
        for(int j=0; j <= numCores; j++)
        {
			coreptr = holeptr->getCore(j);
            if(coreptr == NULL) continue;

			numTies = coreptr->getNumOfTies(tie_type);
			//cout << coreptr->getName() << "  " << coreptr->getNumber() << " " << numTies << endl;
            for(int k=0; k < numTies; k++)
            {
				tieptr = coreptr->getTie(tie_type, k);
				if(tieptr == NULL) 
				{
					continue;
				}
				//cout << " tir : "<< k << ", " << coreptr->getName() << coreptr->getNumber()<< " , " << tieptr->getOrder() << " (size : " << numTies << ")" << endl;
                //cout << tieptr->getType() << " " << tieptr->getOrder() << endl;
				
				if(tieptr->getType() == tie_type && tieptr->getOrder() == order)
                {
					return tieptr;
                }
			}
		}
    }
	return NULL;

}


Value* Correlator::findValueInHole( Hole* holeptr, double depth )
{
	//std::cout << "find value in hole " << std::endl;
	if (holeptr == NULL) return NULL;
 
    Core* coreptr;
	double min, max;
	int numCores =  holeptr->getNumOfCores();
	for(int i=0; i <= numCores; i++)
	{
		coreptr = holeptr->getCore(i);
		if(coreptr == NULL) continue;
		min = coreptr->getMinDepth();
		max = coreptr->getMaxDepth();
		if ((depth >= min) && (depth <= max))
		{
			return findValue(coreptr, depth);
		}
	}
	return NULL;
}

Value* Correlator::findValue( Core* coreptr, double top, int idx  )
{
	if(coreptr == NULL) return NULL;
	if(coreptr->getMinDepth() > top)
		return NULL;
	if(coreptr->getMaxDepth() < top)
		return NULL;	
		
	// find value
 	int size = coreptr->getNumOfValues();
	Value* valueptr = NULL;	
	double valueX, valueY;
	int i=0;
			
	int left = (size- idx) % 2;
	size--;
	if(left == 1) 
	{
		size--;
	}	
	//cout << idx << " " << size << endl;
	
	double topgabX, topgabY;
	Value* valueptrA = NULL;
	Value* valueptrB = NULL;
	for(i=idx ; i <= size; i++) 
	{
		//valueX = coreptr->getValue(i)->getTop();
		//valueY = coreptr->getValue(i+1)->getTop();
		
		valueptrA = coreptr->getValue(i);
		valueptrB = coreptr->getValue(i+1);
		if(valueptrA == NULL || valueptrB == NULL) continue;
		valueX = valueptrA->getELD();
		valueY = valueptrB->getELD();
		
		//cout << valueX << " " << valueY << " " <<  top << endl;
		if(valueX == top) 
		{
			valueptr = valueptrA;	
			break;
		}
		if(valueY == top)
		{
			valueptr = valueptrB;
			break;
		}		
		topgabX =  top - valueX;
		topgabY = top - valueY;
		//cout << "top = " << top << " : " << valueX << ", " << valueY << endl;
		//cout << "value x : " << valueX << " , " << valueY << " :" << top << " ---" << topgabX << "," <<topgabY << endl;
		if(topgabY == 0.0)
		{
			valueptr = valueptrB;
			break;
		}
							
		if((topgabX >= -0.01) && (topgabY < 0.00)) 	//if((top >= valueX) && (top <= valueY))
		{
			//cout << "value x : " << valueX << " , " << valueY << " :" << top << " ---" << topgabX << "," <<topgabY << endl;
			valueptr = valueptrA;
			break;
		}
	} 	 
	 
	if((left == 1) && (valueptr == NULL))
	{
		valueX = valueY;
		valueptrA = valueptrB;
		//valueY = coreptr->getValue(i)->getTop();
		//valueY = coreptr->getValue(i)->getELD();

		valueptrB = coreptr->getValue(i);
		if(valueptrB != NULL) 
		{	
			valueY = valueptrB->getELD();
			if(valueX == top) 
			{
				valueptr = valueptrA;
			} else 
			if(valueY == top)
			{
				valueptr = valueptrB;
			}
			else {			
				topgabX =  top - valueX;
				topgabY = top - valueY;
				if(topgabY == 0.0)
				{
					valueptr = valueptrB;
				} else 
				if((topgabX >= -0.01) && (topgabY <= 0.01))	//if((top >= valueX) && (top <= valueY))
				{
					valueptr = valueptrA;
				}
			}			
		}
	}

	return valueptr;
	
}

Value* Correlator::findValueWithMcd( Core* coreptr, double top, int idx  )
{
	if(coreptr == NULL) return NULL;	
	/*if(coreptr->getMinDepth() > top)
		return NULL;
	if(coreptr->getMaxDepth() < top)
		return NULL;	*/
	
	// find value
 	int size = coreptr->getNumOfValues();
	if(size > 0)
	{
		if(coreptr->getValue(0)->getMcd() > top)
			return NULL;
		if(coreptr->getValue(size -1)->getMcd() < top)
			return NULL;	
	}

	
	Value* valueptr = NULL;	
	double valueX, valueY;
	int i=0;
	
	int left = (size- idx) % 2;
	size--;
	if(left == 1) 
	{
		size--;
	}	
	//cout << idx << " " << size << endl;
	
	double topgabX, topgabY;
	Value* valueptrA = NULL;
	Value* valueptrB = NULL;
	for(i=idx ; i <= size; i++) 
	{
		//valueX = coreptr->getValue(i)->getTop();
		//valueY = coreptr->getValue(i+1)->getTop();
		
		valueptrA = coreptr->getValue(i);
		valueptrB = coreptr->getValue(i+1);
		if(valueptrA == NULL || valueptrB == NULL) continue;
		valueX = valueptrA->getMcd();
		valueY = valueptrB->getMcd();
		if(valueX == top) 
		{
			valueptr = valueptrA;	
			break;
		}
		if(valueY == top)
		{
			valueptr = valueptrB;
		}		
		//cout << valueX << " " << valueY << " " <<  top << endl;
		
		topgabX =  top - valueX;
		topgabY = top - valueY;
		if(topgabY == 0.0)
		{
			valueptr = valueptrB;
			break;
		}
			
		//cout << "top = " << top << " : " << valueX << ", " << valueY << endl;
		//cout << "value x : " << valueX << " , " << valueY << " :" << top << " ---" << topgabX << "," <<topgabY << endl;
		if((topgabX >= -0.01) && (topgabY < 0.00)) 	//if((top >= valueX) && (top <= valueY))
		{
			//cout << "value x : " << valueX << " , " << valueY << " :" << top << " ---" << topgabX << "," <<topgabY << endl;
			valueptr = valueptrA;
			break;
		}
	} 	 
	
	if((left == 1) && (valueptr == NULL))
	{
		valueX = valueY;
		valueptrA = valueptrB;
		//valueY = coreptr->getValue(i)->getTop();
		//valueY = coreptr->getValue(i)->getELD();
		
		valueptrB = coreptr->getValue(i);
		if(valueptrB != NULL) 
		{	
			valueY = valueptrB->getMcd();
			topgabX =  top - valueX;
			topgabY = top - valueY;
			if(valueX == top) 
			{
				valueptr = valueptrA;
			} else 
			if(valueY == top)
			{
				valueptr = valueptrB;
			} else 
			if(topgabY == 0.0)
			{
				valueptr = valueptrB;
			} else 		
			if((topgabX >= -0.01) && (topgabY <= 0.01))	//if((top >= valueX) && (top <= valueY))
			{
				valueptr = valueptrA;
			}
			
		}
	}
	
	return valueptr;
	
}


Value* Correlator::findValueWithMbsf( Core* coreptr, double top, int idx  )
{
	if(coreptr == NULL) return NULL;	
	
	Value* valueptr = NULL;	
	double valueX, valueY;
	int i=0;

	// find value
 	int size = coreptr->getNumOfValues();
	if(size > 0)
	{
		// ---------- UPDATE
		valueptr = coreptr->getValue(0);
		if(valueptr->getMbsf() > top) {
			Value* newValue = coreptr->createValue(size+1, top);
			newValue->copy(valueptr);
			newValue->setValueType(INTERPOLATED_VALUE);
			newValue->setDepth(top);
			newValue->applyAffine(coreptr->getDepthOffset(), valueptr->getType());
			newValue->update();
			return newValue;
			//return NULL;
		}

		valueptr = coreptr->getValue(size -1);		
		if(valueptr->getMbsf() < top) {
			Value* newValue = coreptr->createValue(size+1, top);
			newValue->copy(valueptr);
			newValue->setValueType(INTERPOLATED_VALUE);
			newValue->setDepth(top);
			newValue->applyAffine(coreptr->getDepthOffset(), valueptr->getType());
			newValue->update();
			return newValue;
			return NULL;	
		}
		// ---------- UPDATE
	}
	
	
	int left = (size- idx) % 2;
	size--;
	if(left == 1) 
	{
		size--;
	}	
	//cout << idx << " " << size << endl;
	
	double topgabX, topgabY;
	Value* valueptrA = NULL;
	Value* valueptrB = NULL;
	for(i=idx ; i <= size; i++) 
	{
		//valueX = coreptr->getValue(i)->getTop();
		//valueY = coreptr->getValue(i+1)->getTop();
		
		valueptrA = coreptr->getValue(i);
		valueptrB = coreptr->getValue(i+1);
		if(valueptrA == NULL || valueptrB == NULL) continue;
		valueX = valueptrA->getMbsf();
		valueY = valueptrB->getMbsf();
		if(valueX == top) 
		{
			valueptr = valueptrA;	
			break;
		}
		if(valueY == top)
		{
			valueptr = valueptrB;
		}		
		//cout << valueX << " " << valueY << " " <<  top << endl;
		
		topgabX =  top - valueX;
		topgabY = top - valueY;
		if(topgabY == 0.0)
		{
			valueptr = valueptrB;
			break;
		}
			
		//cout << "top = " << top << " : " << valueX << ", " << valueY << endl;
		//cout << "value x : " << valueX << " , " << valueY << " :" << top << " ---" << topgabX << "," <<topgabY << endl;
		if((topgabX >= -0.01) && (topgabY < 0.00)) 	//if((top >= valueX) && (top <= valueY))
		{
			//cout << "value x : " << valueX << " , " << valueY << " :" << top << " ---" << topgabX << "," <<topgabY << endl;
			valueptr = valueptrA;
			break;
		}
	} 	 
	
	if((left == 1) && (valueptr == NULL))
	{
		valueX = valueY;
		valueptrA = valueptrB;
		//valueY = coreptr->getValue(i)->getTop();
		//valueY = coreptr->getValue(i)->getELD();
		
		valueptrB = coreptr->getValue(i);
		if(valueptrB != NULL) 
		{	
			valueY = valueptrB->getMbsf();
			topgabX =  top - valueX;
			topgabY = top - valueY;
			if(valueX == top) 
			{
				valueptr = valueptrA;
			} else 
			if(valueY == top)
			{
				valueptr = valueptrB;
			} else 
			if(topgabY == 0.0)
			{
				valueptr = valueptrB;
			} else 		
			if((topgabX >= -0.01) && (topgabY <= 0.01))	//if((top >= valueX) && (top <= valueY))
			{
				valueptr = valueptrA;
			}
			
		}
	}
	
	return valueptr;
	
}



Data* Correlator::getDataPtr( void )
{
	return m_dataptr;
}

Hole* Correlator::getSpliceHole( void )
{
	if(m_mainHole[1] == NULL) 
	{
		m_mainHole[1] = new Hole(100, NULL);
		if(m_mainHole[0] != NULL)
		{
			m_mainHole[1]->copy(m_mainHole[0]);
			m_mainHole[1]->update();
			m_mainHole[1]->update();
		}
		m_mainHole[1]->setName("X");
		m_mainHole[1]->setParent(&m_correlatorData);
	}
				
	return m_mainHole[1];
}

Hole* Correlator::getHolePtr( int type )
{
	if (type == SPLICED_RECORD)
	{
		m_mainHole[0]->setType(SPLICED_RECORD);
		return m_mainHole[0];
	} else 
	{
		m_mainHole[1]->setType(ELD_RECORD);
		return m_mainHole[1];
	}
}

void Correlator::setSpliceType( int type )
{
	m_spliceType = type;
}

int Correlator::getSpliceType( void )
{
	return m_spliceType;
}

void Correlator::setDepthStep( double step )
{
	m_depthstep = step;
}

double Correlator::getDepthStep( void )
{
	return m_depthstep;
}

void Correlator::setWinLen( double winlen )
{
	m_winlen = winlen;
}

double Correlator::getWinLen( void )
{
	return m_winlen;
}
	
void Correlator::setLeadLagMeters( double lag )
{
	m_leadlagmeters = lag;
}

double Correlator::getLeadLagMeters( void )
{
	return m_leadlagmeters;
}


void Correlator::setLogData(Data* dataptr)
{
	m_logdataptr = dataptr;
}

Data* Correlator::getLogData( void )
{
	return m_logdataptr;
}
	
void Correlator::update( void )
{
	if(m_mainHole[0])
	{	
		m_mainHole[0]->update();
	}
} 

void Correlator::setCoreOnly( bool flag )
{
	m_isCoreOnly = flag;
}



#ifdef DEBUG
void Correlator::debugPrintOut( void )
{
	if(m_mainHole[0])
	{	
		cout << "\n new spliced hole -----------------------------------------------"<< endl;
		m_mainHole[0]->debugPrintOut();
	}
}
#endif
