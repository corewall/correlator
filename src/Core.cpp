//////////////////////////////////////////////////////////////////////////////////
// CorrelatorLib - Correlator Class Library.  
//
// Module   :  Core.cpp
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

#include <Core.h>
#include <GraValue.h>
#include <PwaveValue.h>
#include <NaturalGammaValue.h>
#include <SusceptibilityValue.h>
#include <ReflectanceValue.h>
#include <Actor.h>
#include <Value.h>
#include <Tie.h>
#include <Strat.h>
#include <Section.h>

#ifdef DEBUG
#include <iostream>
#endif

using namespace std;

Core::Core( int index, CoreObject* parent ) :
  m_number(index), m_goodRef(0),
  m_type(OTHERTYPE), m_smoothStatus(NONE),
  m_stddev(0.0f), m_mean(0.0f), m_logValueptr(NULL), m_cull_tabled(false),
  m_stretch(100.0f), m_mudline(0.0f), m_shiftByaboveCore(false),
  CoreObject(parent), m_quality(GOOD), m_comment()
{
	for(int i=0; i < 2; i++)
	{
		for(int j=0; j < 16; j++)
		{
			m_affine[i].matrix[j] = 0.0f;
		}
		m_affine[i].matrix[0] = 1.0f;
		m_affine[i].matrix[5] = 1.0f;
		m_affine[i].matrix[10] = 1.0f;
		m_affine[i].matrix[15] = 1.0f;
		  
		m_affine[i].applied = false;
		m_affine[i].valuetype = '\0';
		m_affine[i].affinetype = 1;
	}
}

Core::~Core( void )
{
	reset();
	
	vector<Section*>::iterator iter;
	Section* sectionptr= NULL;
	for(iter = m_sections.begin(); iter != m_sections.end(); iter++) 
	{
		sectionptr = (Section*) *iter;
		delete sectionptr;
	}
	vector<Strat*>::iterator iterStrat;
	Strat* tempStrat = NULL;
	for(iterStrat = m_strats.begin(); iterStrat != m_strats.end(); iterStrat++) 
	{
		tempStrat = (Strat*) *iterStrat;
		if(tempStrat) 
		{
			if(tempStrat->getTopCoreId() == getId())
			{
				delete tempStrat;
				tempStrat = NULL;
			}
		}
	}
	m_strats.clear();	
}

void Core::init( int type, bool fromFile )
{
	// initialize data
	// todo
	m_range.ratio = -1.0;
	m_range.min = 9999.0;
	m_range.max = -9999.0;	
	if(type == COMPOSITED_TIE || type == ALL_TIE)
	{	
		for(int i=0; i < 16; i++)
		{
			m_affine[1].matrix[i] = m_affine[0].matrix[i];
		}
		m_affine[1].applied = m_affine[0].applied;
		m_affine[1].valuetype =  m_affine[0].valuetype;
		m_affine[1].affinetype = m_affine[0].affinetype;
	}	

	vector<Value*>::iterator iter;
	Value* tempValue = NULL;
	for(iter = m_values.begin(); iter != m_values.end(); iter++) 
	{
		tempValue = (Value*) *iter;
		if(tempValue) 
		{
			tempValue->init(type);
		}
	}

	m_shiftByaboveCore = false;
	if(type == ALL_TIE)
	{
		cleanTies(COMPOSITED_TIE, fromFile);
		cleanTies(REAL_TIE, fromFile);
	} else if (type != STRETCH)
	{
		cleanTies(type, fromFile);
		if(fromFile == true)
		{
			cleanTies(type, false);
		}
	}
	
	if(type != QUALITY)
	{	
		m_stretch =100.0f;
		m_mudline = 0.0f;
		m_logValueptr = NULL;
	}
	if(type == QUALITY)
	{
		m_smoothStatus = NONE;	
	}	
	m_updated= true;
}

void Core::reset( void )
{
	// delete values
	vector<Value*>::iterator iter;
	Value* tempValue = NULL;
	for(iter = m_values.begin(); iter != m_values.end(); iter++) 
	{
		tempValue = (Value*) *iter;
		if(tempValue) 
		{
			delete tempValue;
			tempValue = NULL;
		}
	}
	m_values.clear();
	
	m_goodRef = 0;
	m_stddev = 0.0f;
	m_mean = 0.0f;
	m_shiftByaboveCore = false;
	m_range.ratio = -1.0;

	for(int i=0; i < 2; i++)
	{
		for(int j=0; j < 16; j++)
		{
			m_affine[i].matrix[j] = 0.0f;
		}
		m_affine[i].matrix[0] = 1.0f;
		m_affine[i].matrix[5] = 1.0f;
		m_affine[i].matrix[10] = 1.0f;
		m_affine[i].matrix[15] = 1.0f;
		  
		m_affine[i].applied = false;
		m_affine[i].valuetype = '\0';
		m_affine[i].affinetype = 1;
	}

	m_logValueptr = NULL;
	cleanTies(COMPOSITED_TIE);
	cleanTies(ALL_TIE);
}

void Core::reset( int type )
{
	m_range.ratio = -1.0;
	// delete values
	vector<Value*>::iterator iter;
	Value* tempValue = NULL;
	for(iter = m_values.begin(); iter != m_values.end(); iter++) 
	{
		tempValue = (Value*) *iter;
		if(tempValue == NULL) continue;
		
		tempValue->reset(type);  
	}
}
	
void Core::copy( CoreObject* objectptr )
{
	Core* coreptr = (Core*) objectptr;
	m_number = coreptr->m_number; 

	m_goodRef = coreptr->m_goodRef;
	m_type = coreptr->m_type;
	m_smoothStatus = coreptr->m_smoothStatus; 
	m_stddev = coreptr->m_stddev;
	m_mean = coreptr->m_mean;
	m_stretch = coreptr->m_stretch;
	m_mudline = coreptr->m_mudline;
	m_shiftByaboveCore = coreptr->m_shiftByaboveCore;
	m_logValueptr = coreptr->m_logValueptr;
	m_annotation = coreptr->m_annotation;
	
	for(int i=0; i < 2; i++)
	{
		for(int j=0; j < 16; j++)
		{
			m_affine[i].matrix[j] = coreptr->m_affine[i].matrix[j];
		}
	  
		m_affine[i].applied = coreptr->m_affine[i].applied;
		m_affine[i].valuetype = coreptr->m_affine[i].valuetype;
		m_affine[i].affinetype = coreptr->m_affine[i].affinetype;
	}

	int size = coreptr->getNumOfValues();
	Value* newValue = NULL;
	for(int i =0; i < size; i++)
	{
		newValue = new Value(i, this);
	    newValue->copy(coreptr->getValue(i));
		m_values.push_back(newValue);	
	}
	copyRange(objectptr);
	m_updated = true;
}


void Core::copyData( CoreObject* objectptr )
{
	if (objectptr == NULL) return;
	Core* coreptr = (Core*) objectptr;
	
	vector<Value*>::iterator iter;
	Value* tempValue = NULL;
	int idx = 0;
	for(iter = m_values.begin(); iter != m_values.end(); iter++, idx++) 
	{
		tempValue = (Value*) *iter;
		if(tempValue == NULL) continue;
		
		tempValue->copyData(coreptr->getValue(idx));  
	}
}

bool Core::isShiftbyTie()
{
	return m_shiftByaboveCore;
}

void Core::cleanTies( int type, bool fromFile )
{
	//std::cout << "clean ties .... called " << std::endl;
	
	// delete tie
	vector<Tie*>::iterator iterTie;
	Tie* tempTie = NULL;
	for(iterTie = m_ties.begin(); iterTie != m_ties.end(); iterTie++) 
	{
		tempTie = (Tie*) *iterTie;
		if(tempTie) 
		{
			if(type == COMPOSITED_TIE)
			{
				if(tempTie->getType() == COMPOSITED_TIE)
				{
					if(tempTie->isFromFile() == fromFile) 
					{
						if (tempTie->getSharedFlag() == false)
						{
							delete tempTie;
							tempTie = NULL;
							m_ties.erase(iterTie);
							if (m_ties.size() > 0)
							{
								iterTie--;
							} else 
							{
								break;
							}
						}
					}
				}
			}
			else if (type == REAL_TIE)
			{
				if(tempTie->getType() == REAL_TIE)
				{
					if(tempTie->isFromFile() == fromFile) 
					{
						if (tempTie->getSharedFlag() == false)
						{
							delete tempTie;
							tempTie = NULL;
							m_ties.erase(iterTie);
							if (m_ties.size() > 0)
							{
								iterTie--;
							} else 
							{
								break;
							}

						}
					}
				}
			}
		}
	}
	
	if(ALL_TIE)
	{
		// delete strat
		/*vector<Strat*>::iterator iterStrat;
		Strat* tempStrat = NULL;
		for(iterStrat = m_strats.begin(); iterStrat != m_strats.end(); iterStrat++) 
		{
			tempStrat = (Strat*) *iterStrat;
			if(tempStrat) 
			{
				if(tempStrat->getTopCoreId() == getId())
				{
					delete tempStrat;
					tempStrat = NULL;
				}
			}
		}
		m_strats.clear();*/
	}
	
}

int Core::getAffineStatus( void )
{
	if(m_affine[1].applied == true)
		return 1;
	return 0;
}

int Core::getRawAffineStatus( void )
{
	if(m_affine[0].applied == true)
		return 1;
	return 0;
	return m_affine[0].affinetype;	
}

int Core::getAffineType( void )
{
	return m_affine[1].affinetype;
}

void Core::setAffineType( int type )
{
	m_affine[0].affinetype = type;
	m_affine[1].affinetype = type;
}
	
void Core::accept( Actor* flt )
{
	if(m_dataValidation == false) return;
	
	if(flt->getDataType() == CORE) 
	{
		flt->visitor(this);
	} else if (flt->getDataType() == TIE)
	{
		vector<Tie*>::iterator iterTie;
		Tie* tempTie = NULL;
		for(iterTie = m_ties.begin(); iterTie != m_ties.end(); iterTie++) 
		{
			tempTie = (Tie*) *iterTie;
			tempTie->accept(flt);
		}	
	} else 
	{
		vector<Value*>::iterator iter;
		Value* tempValue = NULL;
		for(iter = m_values.begin(); iter != m_values.end(); iter++) 
		{
			tempValue = (Value*) *iter;
			tempValue->accept(flt);
		}
	}
	m_updated = true;		
} 
	

void Core::update( void )
{
	if(m_dataValidation == false) return;

	vector<Tie*>::iterator iterTie;
	Tie* tempTie = NULL;
	for(iterTie = m_ties.begin(); iterTie != m_ties.end(); iterTie++) 
	{
		tempTie = (Tie*) *iterTie;
		if(tempTie == NULL) continue;
		tempTie->update();
		if(m_updated == true && m_affine[1].applied == true)
		{
			tempTie->applyAffine(m_affine[1].matrix[11], m_affine[1].valuetype);
		}		
		//tempTie->update();
	}	
	
	vector<Strat*>::iterator iterStrat;
	Strat* tempStrat = NULL;
	for(iterStrat = m_strats.begin(); iterStrat != m_strats.end(); iterStrat++) 
	{
		tempStrat = (Strat*) *iterStrat;
		if(tempStrat) 
		{
			if(m_updated == true && m_affine[1].applied == true)
			{
				if(tempStrat->getTopCoreId() == getId())
				{
					tempStrat->applyTopAffine(m_affine[1].matrix[11]);
				} else 
				{
					tempStrat->applyBotAffine(m_affine[1].matrix[11]);				
				}
			}
		}
	}

	
	if(m_updated == true && m_affine[1].applied == true)
	{
		//cout << " applyAffine " << endl;	
		m_range.mindepth += m_affine[1].matrix[11];
	}

	//cout << "core : 1 " << m_number << endl;
	vector<Value*>::iterator iter;
	Value* tempValue = NULL;
	int test =0;
	for(iter = m_values.begin(); iter != m_values.end(); iter++) 
	{
		tempValue = (Value*) *iter;
		if(tempValue == NULL) continue;
		if(m_updated == true && m_affine[1].applied == true)
		{
			//cout << getName() << getNumber() << " " << m_affine[1].matrix[11] << " " << getType() << endl;
			tempValue->applyAffine(m_affine[1].matrix[11], m_affine[1].valuetype);
		} 
		tempValue->update();
		//cout << "core :  " << test << " " << tempValue->getELD() << endl;
		test++;
	
	}
	if(m_affine[1].matrix[11] == 0)
    {
		m_affine[1].applied = false;
	}
	
	//cout << "core : 2 " << endl;
	
	vector<Section*>::iterator iterSection;
	Section* tempSection= NULL;
	for(iterSection = m_sections.begin(); iterSection != m_sections.end(); iterSection++) 
	{
		tempSection = (Section*) *iterSection;
		if(tempSection == NULL) continue;
		tempSection->update();
	}

	if(m_updated == true)
	{
		calcStdDevMean();
		findAveDepth();	
		
		// to do 
		int value_size = m_values.size();
		if(value_size > 0)
		{
			m_range.mindepth = m_values[0]->getMinDepth();
			value_size = value_size -1;
			m_range.maxdepth = m_values[value_size]->getMaxDepth();
		}
		
		m_range.maxdepthdiff = m_range.maxdepth - m_range.mindepth;
		updateRange();
		
		m_updated = false;
	}
}
	
void Core::getTuple( std::string& data, int type )
{
	char info[255]; info[0] = 0;
	if(type == SPLICE)
	{
		vector<Tie*>::iterator iterTie;
		Tie* tempTie = NULL;
		for(iterTie = m_ties.begin(); iterTie != m_ties.end(); iterTie++)
		{
			tempTie = (Tie*) *iterTie;
			tempTie->getTuple(data, type);
		}
		return;
	} else if (type == STRAT_TABLE)
	{
		//cout << "STRAT_TABLE " << m_strats.size() << endl;
		vector<Strat*>::iterator iterStrat;
		Strat* tempStrat = NULL;
		for(iterStrat = m_strats.begin(); iterStrat != m_strats.end(); iterStrat++)
		{
			tempStrat = (Strat*) *iterStrat;
			if(tempStrat == NULL) continue;
			if(tempStrat->getTopCoreId() == getId())
			{
				tempStrat->getTuple(data, type);
			}
		}
		return;
	} else if (type == SECTION)
	{
		vector<Section*>::iterator iterSection;
		Section* tempSection = NULL;
		for(iterSection = m_sections.begin(); iterSection != m_sections.end(); iterSection++)
		{
			tempSection = (Section*) *iterSection;
			if(tempSection == NULL) continue;
			tempSection->getTuple(data, type);
			//data +=":";
		}
		if(m_sections.size() > 0)
		{
			sprintf(info, "@%.2f,",m_affine[1].matrix[11]);
			data += info;
		}
		return;
	} else if (type == SAGAN_TIE)
	{
		vector<Tie*>::iterator iterTie;
		Tie* tempTie = NULL;
		int tie_type;
		for(iterTie = m_ties.begin(); iterTie != m_ties.end(); iterTie++)
		{
			tempTie = (Tie*) *iterTie;
			if(tempTie == NULL) continue;
			tie_type = tempTie->getType();
			if((tie_type == SAGAN_TIE) || (tie_type == SAGAN_FIXED_TIE))
			{
				tempTie->getTuple(data, type);
			}
		}	
		return;
	} else if (type == TIE_SHIFT)
	{
		vector<Tie*>::iterator iterTie;
		Tie* tempTie = NULL;
		int tie_type;
		for(iterTie = m_ties.begin(); iterTie != m_ties.end(); iterTie++)
		{
			tempTie = (Tie*) *iterTie;
			if(tempTie == NULL) continue;
			tie_type = tempTie->getType();
			if(tie_type == COMPOSITED_TIE)
			{
				tempTie->getTuple(data, type);
			}
		}	
		return;
	}
	
	if(type == SMOOTH) 
	{
		if ((m_smoothStatus != SM_OK) && (m_smoothStatus !=SM_TOOFEWPTS))
		{
			data +=":";
			return;
		}
		/*if (m_smoothStatus == SM_TOOFEWPTS)
		{
			cout << "[ERROR] Too Few Points for Smoothing" << endl;
		}*/
	}

	// brg unused
	//int affine = 0;
	//if((m_affine[1].applied == true) && (m_shiftByaboveCore == false))
	//	affine = 1;

	if (m_values.size() > 0)
	{
		//sprintf(info, "%.2f,%.2f,%.2f,%.2f,%d,%.2f,%s,%d,", getTop(), getBottom(), m_range.realminvar,m_range.realmaxvar , affine, m_stretch, m_annotation.c_str(), m_quality); 
		sprintf(info, "%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%s,%d,", getTop(), getBottom(), m_range.realminvar,m_range.realmaxvar , m_affine[1].matrix[11], m_stretch, m_annotation.c_str(), m_quality); 

		data += info;
	
		vector<Section*>::iterator iterSection;
		Section* tempSection = NULL;
		for(iterSection = m_sections.begin(); iterSection != m_sections.end(); iterSection++)
		{
			tempSection = (Section*) *iterSection;
			if(tempSection == NULL) continue;
			tempSection->getTuple(data, type);
		}
		data +=":";
	}
				
	vector<Value*>::iterator iter;
	Value* tempValue = NULL;
	for (iter = m_values.begin(); iter != m_values.end(); iter++)
	{
		tempValue = (Value*) *iter;
		if (tempValue == NULL) continue;
		tempValue->getTuple(data, type);
	}
	data += ":";
}

void Core::setRange( data_range range )
{
	if(m_range.top > range.top)	 // min
	{
		m_range.top = range.top;
	}
	if(m_range.bottom < range.bottom)	// max
	{
		m_range.bottom = range.bottom;
	}

	/*if(m_range.mindepth > range.mindepth)
	{
		m_range.mindepth = range.mindepth;
	}
	if(m_range.maxdepth < range.maxdepth)
	{
		m_range.maxdepth = range.maxdepth;
	}*/	

	if(m_range.min > range.min)
	{
		m_range.min = range.min;
	}
	if(m_range.max < range.max)
	{
		m_range.max = range.max;
	}
	//cout << "core" << getNumber() <<" : min=" << m_range.min << " max=" << m_range.max  << " " << range.min << " " << range.max << endl;
		
	m_range.realminvar = m_range.min;
	m_range.realmaxvar = m_range.max;

	//cout << "data ratio = " << m_range.ratio << " " <<  range.ratio << " => " ;	
	if(m_range.ratio <= 0) 
	{
		m_range.ratio = range.ratio;
	} else 
	{
		m_range.ratio += range.ratio;
		m_range.ratio /= 2;
	}
	//cout <<  m_range.ratio << endl ;	

		
	m_range.avedepstep = range.avedepstep;
	
	m_updated = true;
}
	
Value* Core::createTypedValue(const int index)
{
	Value *newValue = NULL;
	switch (m_type)
	{
	case GRA:
		{
			newValue = (Value*) new GraValue(index, this);
			break;
		}
	case PWAVE:
		{
			newValue = (Value*) new PwaveValue(index, this);
			break;
		}
	case SUSCEPTIBILITY:
		{
			newValue = (Value*) new SusceptibilityValue(index, this);
			break;
		}
	case NATURALGAMMA:
		{
			newValue = (Value*) new NaturalGammaValue(index, this);
			break;
		}
	case REFLECTANCE:
		{
			newValue = (Value*) new ReflectanceValue(index, this);
			break;
		}
	default:
		{
			newValue = (Value*) new NaturalGammaValue(index, this);
			break;
		}
	}
	return newValue;
}

Value* Core::createValue( int index )
{
	// check validation with index
	vector<Value*>::iterator iter;
	Value* valueptr= NULL;
	for(iter = m_values.begin(); iter != m_values.end(); iter++) 
	{
		valueptr = (Value*) *iter;
		if(valueptr == NULL) continue;
		if(valueptr->getNumber()  == index) 
		{
			return valueptr;
			//return NULL;
		}
	}
	
	Value* newValue = createTypedValue(index);
	if (newValue != NULL) 
	{
		m_values.push_back(newValue);
		m_goodRef++;
	}
	
	m_updated = true;
	return newValue;
}

Value* Core::createValue( int index, double depth )
{
	// check validation with index
	vector<Value*>::iterator iter;
	Value* valueptr= NULL;
	for(iter = m_values.begin(); iter != m_values.end(); iter++) 
	{
		valueptr = (Value*) *iter;
		if(valueptr == NULL) continue;
		if(valueptr->getMbsf()  == depth) 
		{
			//cout << "exist value---- " << endl;
			return valueptr;
			//return NULL;
		}
	}
	
	Value* newValue = createTypedValue(index);
	if (newValue != NULL) 
	{
		for(iter = m_values.begin(); iter != m_values.end(); iter++) 
		{
			valueptr = (Value*) *iter;
			if(valueptr == NULL) continue;
			if(valueptr->getMbsf()  > depth) 
			{
				m_values.insert(iter, newValue);
				m_goodRef++;
				m_updated = true;
#ifdef DEBUG
				cout << "[DEBUG] Depth order changed : core No=" << getNumber() << " point depth=" << valueptr->getMbsf()  << " depth=" << depth <<  endl;
#endif
				return newValue;
			}
		}
		m_values.push_back(newValue);
		m_goodRef++;
	}
	
	m_updated = true;
	return newValue;
}

int Core::deleteInterpolatedValue( int number )
{
	
	// check validation with index
	vector<Value*>::iterator iter;
	Value* valueptr= NULL;
	iter = m_values.begin();
	int index = 0;
	while(iter != m_values.end())
	{
		valueptr = (Value*) *iter;
		if(valueptr == NULL) continue;
		if((valueptr->getValueType() == INTERPOLATED_VALUE) && (valueptr->getNumber() == number))
		{
			m_values.erase(iter);
#ifdef DEBUG			
			cout << "[DEBUG] Interpolated  value is deleted : core No=" << getName() << getNumber() <<  " depth="  << " /" << valueptr->getMbsf() << " " <<  valueptr->getNumber() << endl;
#endif
			delete valueptr;
			valueptr = NULL;	
			continue;		
		}
		valueptr->setNumber(index);
		iter++;
		index++;
	}
	//std::cout << "deleted ... " << std::endl;
	return 1;
}

Value* Core::createInterpolatedValue( double depth )
{
	// check validation with index
	vector<Value*>::iterator iter;
	Value* valueptr= NULL;
	for(iter = m_values.begin(); iter != m_values.end(); iter++) 
	{
		valueptr = (Value*) *iter;
		if(valueptr == NULL) continue;
		if(valueptr->getValueType() != INTERPOLATED_VALUE) continue;
		//cout << valueptr->getMbsf()  << " " <<  depth << endl;
		 
		if(valueptr->getMbsf()  == depth)
		{
			//cout << "exist interpolated... value---- " << endl;
			return valueptr;
			//return NULL;
		}
	}
	
	int index =0;	
	Value* newValue = NULL;
	for(iter = m_values.begin(); iter != m_values.end(); iter++, index++) 
	{
		valueptr = (Value*) *iter;
		if(valueptr == NULL) continue;
		if(valueptr->getMbsf()  > depth) 
		{
			if(newValue == NULL)
			{
				newValue = createTypedValue(index);
				if (newValue != NULL)
				{
					newValue->setValueType(INTERPOLATED_VALUE);				
					m_values.insert(iter, newValue);
					m_goodRef++;
					m_updated = true;
#ifdef DEBUG				
					cout << "[DEBUG] Interpolated  value is added : core No=" << getNumber() << " depth=" << depth <<  " before point depth=" << valueptr->getMbsf() << " " << index <<  endl;
#endif
				}
				break;
			}
		}
	}

	index = 0;
	for(iter = m_values.begin(); iter != m_values.end(); iter++, index++) 
	{
		valueptr = (Value*) *iter;
		if(valueptr == NULL) continue;
		valueptr->setNumber(index);
	}
	
	if(newValue == NULL)
	{
		newValue = createTypedValue(index);
		if (newValue != NULL)
		{
			newValue->setValueType(INTERPOLATED_VALUE);				
			m_values.push_back(newValue);
			m_goodRef++;
#ifdef DEBUG		
			cout << "[DEBUG] Interpolated  value is added : core No=" << getNumber() << " depth=" << depth <<  " before point depth=" << newValue->getMbsf() << " " << index <<  endl;
#endif
		}
		m_updated = true;
	}
	return newValue;	
}

void Core::deleteValue( int index )
{
	vector<Value*>::iterator iter;
	Value* valueptr= NULL;
	for(iter = m_values.begin(); iter != m_values.end(); iter++) 
	{
		valueptr = (Value*) *iter;
		if(valueptr == NULL) continue;
		if(valueptr->getNumber()  == index) 
		{
			m_values.erase(iter);
			delete valueptr;
			valueptr = NULL;	
			return;	
		}
	}	
}

Section* Core::createSection( int index )
{
	// check validation with index
	vector<Section*>::iterator iter;
	Section* sectionptr= NULL;
	for(iter = m_sections.begin(); iter != m_sections.end(); iter++) 
	{
		sectionptr = (Section*) *iter;
		if(sectionptr->getNumber()  == index) 
		{
			return sectionptr;
		}
	}
	
	Section* newSection = new Section(index, this);	
	for(iter = m_sections.begin(); iter != m_sections.end(); iter++) 
	{
		sectionptr = (Section*) *iter;
		if(sectionptr->getNumber() > index) 
		{
			m_sections.insert(iter, newSection);
			m_updated = true;
			return newSection;
		}
	}
	
	m_sections.push_back(newSection);
	m_updated = true;	
	return newSection;
}


void Core::deleteSection( int index )
{	
	// check validation with index
	vector<Section*>::iterator iter;
	Section* sectionptr= NULL;
	for(iter = m_sections.begin(); iter != m_sections.end(); iter++) 
	{
		sectionptr = (Section*) *iter;
		if(sectionptr->getNumber()  == index) 
		{
			m_sections.erase(iter);
			delete sectionptr;
			sectionptr = NULL;
			//cout << "section is deleted  " <<  index << endl;
			return;
		}
	}
}

void Core::setLogValue( Value* valueptr )
{
	m_logValueptr = valueptr;
}

Value* Core::getLogValue( void )
{
	return m_logValueptr;
}
		
int	Core::validate( void )
{
	return checkDepthOrder();
}

int Core::calcStdDevMean( int off )
{
	int n = m_values.size();

	int size = off + n;
	if(n < 1 || size > n) 
	{
		return 0;
	} 

	double sum = 0.0;
	double sumsq = 0.0;
	int nx = 0;

	for(int i = off; i < size; i++) 
	{
		if(m_values[i]->getData() != BAD_PT) 
		{
			sum = sum + m_values[i]->getData();
			sumsq = sumsq + m_values[i]->getData() * m_values[i]->getData();
			nx++;
		}
	} 
	if(nx < 2) 
	{
		return 1;
	}
	
	m_mean = sum / nx;
 
	m_stddev = (nx * sumsq - sum * sum) / (nx * (nx - 1));
	if(m_stddev < 0.0) 
	{
		m_stddev = 0.0;
	} else 
	{
		m_stddev = sqrt(m_stddev);
	}
	
	// BUG
	//m_range.min = m_mean - (PLUSMINUS_STD * m_stddev);
	//m_range.max = m_mean + (PLUSMINUS_STD * m_stddev);
	
	return 0;
}

int Core::findAveDepth( int off )
{
	int n = m_values.size();
	int size = n- off;
	if(n < 1 || size > n) 
	{
		return 0;
	} 

	// calculate the average depth step
	double pavedt = 0.0;
	double nave = 0.0;
	int exp;
	size = size - off -1;
	for(int i = off; i < size; i++) 
	{
		exp = m_values[i]->getQuality() & ~BAD_SMOOTH;
		if(exp == GOOD) 
		{
			pavedt = pavedt +  m_values[i+1]->getMbsf() - m_values[i]->getMbsf();
		}
	} 
	
	//cout << "pavedt= " << pavedt << " size= " << size << endl;

	nave = size - 1.0;
    if (nave >= 1.0)
	{
		pavedt = pavedt / nave;
    } else
	{
		// warning; can not calculate average depth. using 0.05m.
		pavedt = 0.05;
		m_range.avedepstep = pavedt;
		return 1;
	}

	// round ave depth up to nearest cm
	//round(pavedt, 0.01);
	round(pavedt);
	m_range.avedepstep = pavedt;

	return 1;
}
	
// check that depth is in descending order
int Core::checkDepthOrder( void ) 
{
	int numvalues = m_values.size();	
	int i = 0;
	int iminus, iplus, ith;
	
	// check data quality : 
	while(i < numvalues &&  (m_values[i]->getQuality() & BAD_SB_DEPTH)) i++;
	iminus = i;
	i++;
			
	int errCount =0;		
	while(i <  numvalues) 
	{

		while(i < numvalues &&  (m_values[i]->getQuality() & BAD_SB_DEPTH)) i++;
		ith = i;
		i++;
				
		while(i < numvalues &&  (m_values[i]->getQuality() & BAD_SB_DEPTH)) i++;
		iplus = i;
		i++;

		// validate index
		if(iminus == ith || ith == iplus) break;
		if(iplus >= numvalues) break;	

		// compare depth order  
		if((m_values[ith]->getDepth() < m_values[iminus]->getDepth()) || (m_values[ith]->getDepth() > m_values[iplus]->getDepth())) 
		{
#ifdef DEBUG		
			cout << "---- error : " <<  m_values[iminus]->getDepth() << " " << m_values[ith]->getDepth() << " " << m_values[iplus]->getDepth() << endl;
#endif		
			errCount++;	
		}
		
		if(errCount >= TOO_MANY_OUTOF_ORDER) break;
		
		iminus = iplus;
	}

	// think about errCount... what to do with the value
	if(errCount > 0) {
		m_dataValidation = false;
		return 0;
	 }
	
	return 1;
}

void Core::setNumber( int index )
{
	m_number = index;
}


int Core::getNumber( void )
{
	return m_number;
}

Value* Core::getValue( int index )
{
	if(index < m_values.size())
	{
		return m_values[index];
	}
	
	// check validation with index
	/*vector<Value*>::iterator iter;
	Value* valueptr= NULL;
	for(iter = m_values.begin(); iter != m_values.end(); iter++) 
	{
		valueptr = (Value*) *iter;
		if(valueptr->getNumber()  == index) 
		{
			return (Value*) *iter;
		}
	}*/
	
	return NULL;
}

Value* Core::getValue( int section_id, double top )
{
	vector<Value*>::iterator iter;
	Value* valueptr= NULL;
	for(iter = m_values.begin(); iter != m_values.end(); iter++) 
	{
		valueptr = (Value*) *iter;
		if(valueptr->getSectionID() == section_id) 
		{
			if(valueptr->getTop() == top)
				return (Value*) *iter;
				
			if(fabs(valueptr->getTop() - top) <= CULL_TABLE_DEPTH_CHECK)
				return (Value*) *iter;
		}
	}	
	return NULL;
}
	
Value* Core::getLast(void)
{
	int index = m_values.size() -1;
	return m_values[index];
}

Value* Core::getFirst(void)
{
	if (m_values.size() == 0) return NULL;
	
	return m_values[0];
}	

int	Core::getNumOfValues( void )
{
	int size = m_values.size();
	return size;
}

char Core::getCoreType( void )
{
	if(m_values.size() == 0) return 'X';
	return m_values[0]->getType();
}
	
Section* Core::getSection( int index )
{
	// check validation with index
	vector<Section*>::iterator iter;
	Section* sectionsptr= NULL;
	for(iter = m_sections.begin(); iter != m_sections.end(); iter++) 
	{
		sectionsptr = (Section*) *iter;
		if(sectionsptr->getNumber()  == index) 
		{
			return sectionsptr;
		}
	}
	
	return NULL;
}

int	Core::getNumOfSections( void )
{
	int size = m_sections.size();
	return size;
}

void Core::setType( int type )
{
	m_type = type;
}

int	Core::getType( void )
{
	return m_type;
}

void  Core::setOffsetByAboveTie(double offset, char valuetype)
{
	if( m_affine[1].applied == false) 
	{
		//m_shiftByaboveCore = true;
	}
	offset = offset + m_affine[1].matrix[11];
	//std::cout << offset << std::endl; 	
	setDepthOffset(offset, valuetype, true);
	m_affine[1].affinetype = 0;
}

void Core::setDepthOffset( double offset, bool applied, bool fromfile )
{
	m_affine[1].matrix[12] = m_affine[1].matrix[11];

	m_affine[1].matrix[11] = offset;	
	m_affine[1].applied = applied;
	m_affine[1].affinetype = 1;

	if(fromfile == true)
	{
		m_affine[0].matrix[11] = offset;
		m_affine[0].applied = applied;		
		m_affine[0].affinetype = 1;
	}
	m_updated = true;
}

void Core::setDepthOffset( double offset, char valuetype, bool applied, bool fromfile )
{
	m_affine[1].matrix[12] = m_affine[1].matrix[11]; // matrix[12] = previous offset?

	m_affine[1].matrix[11] = offset;
	m_affine[1].valuetype = valuetype;	
	m_affine[1].applied = applied;
	m_affine[1].affinetype = 1;
	if(fromfile == true)
	{
		m_affine[0].matrix[11] = offset;		
		m_affine[0].valuetype = valuetype;
		m_affine[0].applied = applied;	
		m_affine[1].affinetype = 1;
	}
	m_updated = true;
}

void Core::initDepthOffset( void )
{
	m_affine[1].matrix[12] = 0.0;
	m_affine[1].matrix[11] = 0.0;	
	m_affine[1].applied = true;
	m_affine[1].affinetype = 1;
	m_updated = true;	
	//update();
}

void Core::updateLight( void )
{
	vector<Value*>::iterator iter;
	Value* tempValue = NULL;
	for(iter = m_values.begin(); iter != m_values.end(); iter++) 
	{
		tempValue = (Value*) *iter;
		if(m_updated == true && m_affine[1].applied == true)
		{
			tempValue->applyAffine(m_affine[1].matrix[11], m_affine[1].valuetype);
		} 
		tempValue->updateLight();
	}
	m_updated = false;	
}

double Core::getDepthOffset( void )
{
	return m_affine[1].matrix[11];
}

double Core::getRawDepthOffset( void )
{
	return m_affine[0].matrix[11];
}
	
void Core::undo( bool fromfile )
{
	if(fromfile == false) 
	{
		m_affine[1].matrix[11] = m_affine[1].matrix[12];
	} else 
	{
		m_affine[1].matrix[11] = m_affine[0].matrix[11];
	}
	m_updated = true;
}

void Core::setSmoothStatus( int status )
{
	m_smoothStatus = status;
	m_updated = true;	
}

int	Core::getSmoothStatus( void )
{
	return m_smoothStatus;
}

void Core::setStretch( double stretch )
{
	m_stretch = stretch;
	
	vector<Value*>::iterator iter;
	Value* tempValue = NULL;
	for(iter = m_values.begin(); iter != m_values.end(); iter++) 
	{
		tempValue = (Value*) *iter;
		tempValue->setStretch(m_stretch);
	}
	
	vector<Tie*>::iterator iterTie;
	Tie* tempTie = NULL;
	for(iterTie = m_ties.begin(); iterTie != m_ties.end(); iterTie++) 
	{
		tempTie = (Tie*) *iterTie;
		tempTie->setStretch(m_stretch);
	}	
		
	// todo how about tie
	m_updated = true;
}

double Core::getStretch( void )
{
	return m_stretch;
}

void Core::setMudLine( double line )
{
	m_mudline = line;
}

double Core::getMudLine( void )
{
	return m_mudline;
}

double Core::getStd( void )
{
	return m_stddev;
}

void Core::refGood( void )
{
	m_goodRef++;
	if(m_goodRef > m_values.size()) 
	{
		m_goodRef = m_values.size();
	}
}

void Core::unrefGood( void )
{
	m_goodRef--;
	if(m_goodRef < 0)
	{
		m_goodRef = 0;
	}
}
	
void Core::setQuality( int quality )
{
	if (quality == BAD_CULLTABLE)
	{
		m_cull_tabled = true;
		quality = BAD;
	}
	m_quality = quality;
	//cout << " quality =========== " << m_quality << " " << getName() << " " << getNumber() << endl;
}

int Core::getQuality( void )
{
	return m_quality;
}

void Core::setComment(const std::string &comment)
{
	m_comment = comment;
}

std::string Core::getComment() { return m_comment; }
	
int	Core::getNumOfTies( void )
{
	return m_ties.size();
}


int	Core::getNumOfTies( int type )
{
	int count = 0;
	vector<Tie*>::iterator iter;
	Tie* tempTie = NULL;
	for(iter = m_ties.begin(); iter != m_ties.end(); iter++) 
	{
		tempTie = (Tie*) *iter;
		if(tempTie->getType() == type) 
		{
			count++;
		}
	}
	return count;
}

int	Core::addTie( Tie* object )
{
	if(object == NULL) return 0;
	
	int success = 0;
	vector<Tie*>::iterator iter;
	Tie* tempTie = NULL;
	TieInfo* infoTieToA = NULL;
	TieInfo* infoTieToB = NULL;
	if(object->getType() == SAGAN_TIE)
	{
		infoTieToB = object->getInfoTied();
		for(iter = m_ties.begin(); iter != m_ties.end(); iter++) 
		{
			tempTie = (Tie*) *iter;
			if(tempTie && (tempTie->getType() == SAGAN_TIE))
			{
				infoTieToA = tempTie->getInfoTied();
				if(infoTieToA)
				{
					if(infoTieToA->m_valueptr->getELD() > infoTieToB->m_mcd) 
					{
						//cout << infoTieToA->m_mcd << " > " << infoTieToB->m_mcd << endl;
						m_ties.insert(iter, object);
						success = 1;
						break;
					}
				}
			}
		}	
	}
	else 
	{	
		infoTieToB = object->getInfoTieTo();
		for(iter = m_ties.begin(); iter != m_ties.end(); iter++) 
		{
			tempTie = (Tie*) *iter;
			if(tempTie)
			{
				infoTieToA = tempTie->getInfoTieTo();
				if(infoTieToA)
				{
					if(infoTieToA->m_mcd > infoTieToB->m_mcd) 
					{
						m_ties.insert(iter, object);
						success = 1;
						break;
					}
				}
			}
		}	
	}
	
	if(success == 0)
	{
		m_ties.push_back(object);
	}
	
	
	m_updated = true;	
	return 1;
}

void Core::disableTies( void )
{
	vector<Tie*>::iterator iterTie;
	Tie* tempTie = NULL;
	int tie_type;
	for(iterTie = m_ties.begin(); iterTie != m_ties.end(); iterTie++)
	{
		tempTie = (Tie*) *iterTie;
		if(tempTie == NULL) continue;
		tie_type = tempTie->getType();
		if(tie_type == COMPOSITED_TIE) 
		{
			tempTie->disable();
		}
	}	
}
	
int	Core::deleteTie( int index )
{
	// todo
	//std::cout << ".......called delete Tie " << getName() << getNumber() << std::endl;
	
	vector<Tie*>::iterator iter;
	Tie* tempTie = NULL;
	for(iter = m_ties.begin(); iter != m_ties.end(); iter++) 
	{
		tempTie = (Tie*) *iter;
		if(tempTie == NULL) continue; 
		if(tempTie->getId() == index) 
		{
			m_ties.erase(iter);
			m_updated = true;	
			return 1;
		}
	}

	return 0;
}

int	Core::deleteTies( int type )
{
	// BUG.....
	//std::cout << "...... called delete Tie type " << type << std::endl;
	
	// todo
	vector<Tie*>::iterator iter;
	Tie* tempTie = NULL;
	for(iter = m_ties.begin(); iter != m_ties.end(); iter++) 
	{
		tempTie = (Tie*) *iter;
		if(tempTie == NULL) continue; 
		if(tempTie->getType() == type) 
		{
			m_ties.erase(iter);
		}
	}

	return 0;
}

Tie* Core::getTie( int index )
{
	vector<Tie*>::iterator iter;
	Tie* tempTie = NULL;
	int i = 0;
	for(iter = m_ties.begin(); iter != m_ties.end(); iter++, i++) 
	{
		tempTie = (Tie*) *iter;
		if(i == index) 
		{
			return tempTie;
		}
	}
	return NULL;
}

Tie* Core::getTie( int type, int index )
{
	vector<Tie*>::iterator iter;
	Tie* tempTie = NULL;
	int i = 0;
	for(iter = m_ties.begin(); iter != m_ties.end(); iter++) 
	{
		tempTie = (Tie*) *iter;
		if(tempTie->getType() == type) 
		{
			if(i == index)
			{
				return tempTie;
			}
			i++;
		}
	}
	return NULL;
}
	
int	Core::addStrat( Strat* object )
{
	if(object == NULL) return 0;
	
	m_strats.push_back(object);
	m_updated = true;	
	return 1;
}

int	Core::getNumOfStrat( void )
{
	return m_strats.size();
}	

int	Core::deleteStrat( int index )
{
	// todo
	/*vector<Strat*>::iterator iter;
	Strat* tempStrat = NULL;
	for(iter = m_strats.begin(); iter != m_strats.end(); iter++) 
	{
		Strat = (Strat*) *iter;
		if(Strat) 
		{
			delete Strat;
			Strat = NULL;
		}
	}*/
	m_updated = true;	

	return 1;
}

int	Core::deleteStrat( void )
{
	vector<Strat*>::iterator iter;
	Strat* tempStrat = NULL;
	for(iter = m_strats.begin(); iter != m_strats.end(); iter++) 
	{
		tempStrat = (Strat*) *iter;
		if(tempStrat) 
		{
			if(tempStrat->getTopCoreId() == getId())
			{
				delete tempStrat;
				tempStrat = NULL;
			}
		}
	}
	m_strats.clear();
	m_updated = true;	

	return 1;
}

Strat* Core::getStrat( int index )
{
	int i = 0;
	vector<Strat*>::iterator iter;
	Strat* tempStrat = NULL;
	for(iter = m_strats.begin(); iter != m_strats.end(); iter++, i++) 
	{
		tempStrat = (Strat*) *iter;
		if(i == index) 
		{
			return tempStrat;
		}
	}
	return NULL;
}
	
const char* Core::getSite( void )
{
	if(m_parent) 
	{
		return m_parent->getSite();
	}
	return NULL;
}

const char* Core::getLeg( void )
{
	if(m_parent) 
	{
		return m_parent->getLeg();	
	}
	return NULL;
}

const char* Core::getName( void )
{
	if(m_parent) 
	{
		return m_parent->getName();	
	}
	return NULL;
}
	
int	Core::getDataFormat( void )
{
	if(m_parent) 
	{
		return m_parent->getDataFormat();
	}
	return -1;
}	

int Core::check(char* leg, char* site , char* holename , int corenumber,  char* section)
{
	char* name_ptr = (char*) getName();
	if( (m_number == corenumber) && (strcmp(holename,name_ptr) ==0) && (strcmp(leg, getLeg()) ==0) && (strcmp(site, getSite()) ==0) )
	{
		return 1;
	}
	return 0;
}
	
#ifdef DEBUG
void Core::debugPrintOut( void )
{
	cout << "[Core] index : " << m_number << "  number of values : " << m_values.size() << "  stddev : " << m_stddev << "  mean : " << m_mean;
	switch(m_type) 
	{
	case GRA:
		cout << "  core type : GRA " << endl;		
		break;
	case PWAVE:
		cout << "  core type : PWAVE " << endl;		
		break;
	case SUSCEPTIBILITY:
		cout << "  core type : SUSCEPTIBILITY " << endl;		
		break;
	case NATURALGAMMA:
		cout << "  core type : NATURALGAMMA " << endl;		
		break;
	case REFLECTANCE:
		cout << "  core type : REFLECTANCE " << endl;		
		break;		
	case OTHERTYPE:
		cout << "  core type : OTHERTYPE " << endl;		
		break;					
	}
	cout << "[Core] top : " << m_range.top << "  bottom : " << m_range.bottom <<  "  min depth : " << m_range.mindepth << "  max depth : " << m_range.maxdepth << "  stretch/compress : " << m_stretch << endl;
	cout << "[Core] min : " <<  m_range.min << " (real:" << m_range.realminvar << ")  max : " << m_range.max << " (real:" << m_range.realmaxvar << ")  ave depth : " << m_range.avedepstep << "  mbsf/mcd : " << m_range.ratio << endl;

	for(int i=0; i < 2; i++)
	{
		cout << " depth offset[" << i << "] : " << m_affine[i].matrix[11] << "  selected value type : " << m_affine[i].valuetype;
		if(m_affine[i].applied == true)
		{
			cout << " offset applied : Y " << endl;
		} else 
		{
			cout << " offset applied : N " << endl;
		}
	}

	vector<Tie*>::iterator iter;
	Tie* tempTie = NULL;
	for(iter = m_ties.begin(); iter != m_ties.end(); iter++) 
	{
		tempTie = (Tie*) *iter;
		tempTie->debugPrintOut();
	}
	
	vector<Value*>::iterator iterValue;
	Value* valueptr = NULL;	
	for(iterValue = m_values.begin(); iterValue != m_values.end(); iterValue++) 
	{
		valueptr = (Value*) *iterValue;	
		valueptr->debugPrintOut();
	}	
	
	vector<Strat*>::iterator iterStart;
	Strat* tempStrat = NULL;
	for(iterStart = m_strats.begin(); iterStart != m_strats.end(); iterStart++) 
	{
		tempStrat = (Strat*) *iterStart;
		tempStrat->debugPrintOut();
	}	
}
#endif
