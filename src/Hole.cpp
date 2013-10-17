//////////////////////////////////////////////////////////////////////////////////
// CorrelatorLib - Correlator Class Library.  
//
// Module   :  Hole.cpp
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

#include <Hole.h>
#include <Actor.h>

#ifdef DEBUG
#include <iostream>
#endif

using namespace std;

Hole::Hole( int index, CoreObject* parent ) :
  m_number(index), m_topAvailable(true),
  m_dataFormat(-1), m_name(""), m_type(-1),
  CoreObject(parent), m_eldStatus(false)
{
}

Hole::~Hole( void )
{
	reset();
}

void Hole::init( int type, bool fromFile )
{
	m_eldStatus = false;
	m_range.ratio = -1.0;
	m_range.min = 9999.0;
	m_range.max = -9999.0;

	// initialize data
	// todo
	vector<Core*>::iterator iCore;
	Core* tempCore = NULL;
	for(iCore = m_cores.begin(); iCore != m_cores.end(); iCore++) 
	{
		tempCore = (Core*) *iCore;
		if(tempCore) 
		{
			tempCore->init(type, fromFile);
		}
	}
	m_updated = true;
	
}

void Hole::init( int type, int coretype, char* annotation, bool fromFile )
{
	bool act = false;
	m_range.ratio = -1.0;
	m_range.min = 9999.0;
	m_range.max = -9999.0;

	if((coretype == USERDEFINEDTYPE) && (m_annotation == annotation))
	{
		act = true;	
	} 
	else if (m_type == coretype)
	{
		act = true;
#ifdef DEBUG		
		cout << coretype << " is same " << endl;
#endif
	}
	
	if(act == true)
	{
		vector<Core*>::iterator iCore;
		Core* tempCore = NULL;
		for(iCore = m_cores.begin(); iCore != m_cores.end(); iCore++) 
		{
			tempCore = (Core*) *iCore;
			if(tempCore) 
			{
				tempCore->init(type, fromFile);
			}
		}	
	}
	m_updated = true;
}

void Hole::reset( void )
{
	m_eldStatus = false;
	m_range.ratio = -1.0;
	// delete cores
	vector<Core*>::iterator iCore;
	Core* tempCore = NULL;
	for(iCore = m_cores.begin(); iCore != m_cores.end(); iCore++) 
	{
		tempCore = (Core*) *iCore;
		if(tempCore) 
		{
			delete tempCore;
			tempCore = NULL;
		}
	}
	m_cores.clear();
}

void Hole::reset( int type )
{
	m_range.ratio = -1.0;
	// delete cores
	vector<Core*>::iterator iCore;
	Core* tempCore = NULL;
	for(iCore = m_cores.begin(); iCore != m_cores.end(); iCore++) 
	{
		tempCore = (Core*) *iCore;
		if(tempCore == NULL) continue;
		
		tempCore->reset(type);  
	}
}

void Hole::copy( CoreObject* objectptr )
{
	Hole* holeptr = (Hole*) objectptr;
	m_number = holeptr->m_number; 
	
	m_dataFormat = holeptr->m_dataFormat;
	m_name = holeptr->m_name; 
	m_type = holeptr->m_type;
	m_eldStatus = holeptr->m_eldStatus;

	int size = holeptr->getNumOfCores();
	Core* newCore = NULL;
	for(int i =0; i < size; i++)
	{
		newCore = new Core(i, this);
	    newCore->copy(holeptr->getCore(i));
		m_cores.push_back(newCore);	
	}
	copyRange(objectptr);	
	m_updated = true;	
}
	
void Hole::copyData( CoreObject* objectptr )
{
	if (objectptr == NULL) return;
	
	Hole* holeptr = (Hole*) objectptr;
	vector<Core*>::iterator iter;
	const char* annot = holeptr->getAnnotation();
#ifdef DEBUG	
	cout << "annotation = " << annot << endl;
#endif	
	Core* tempCore = NULL;
	int idx = 0;
	for(iter = m_cores.begin(); iter != m_cores.end(); iter++, idx++) 
	{
		tempCore = (Core*) *iter;
		if(tempCore == NULL) continue;
		
		tempCore->copyData(holeptr->getCore(idx));  
	}
}


void Hole::accept( Actor* flt )
{
	if(flt->getDataType() == HOLE) 
	{
		flt->visitor(this);
	} else 
	{
		vector<Core*>::iterator iCore;
		Core* tempCore = NULL;
		for(iCore = m_cores.begin(); iCore != m_cores.end(); iCore++) 
		{
			tempCore = (Core*) *iCore;
			tempCore->accept(flt);
		}
	}
} 
	
void Hole::update( void )
{
	vector<Core*>::iterator iter;
	Core* tempCore = NULL;
	for(iter = m_cores.begin(); iter != m_cores.end(); iter++) 
	{
		tempCore = (Core*) *iter;
		if(tempCore == NULL) continue;
		tempCore->update();
	}
	if(m_updated == true)
	{
		// to do 
		updateRange();
		m_updated = false;
	}
} 


void Hole::getTuple( std::string& data, int type )
{
	vector<Core*>::iterator iter;
	Core* tempCore = NULL;
	if(type == SPLICE)
	{
		for(iter = m_cores.begin(); iter != m_cores.end(); iter++)
		{   
			tempCore = (Core*) *iter;
			tempCore->getTuple(data, type);
		}
		return;
	} 

	std::string coretype = "";
	if(type == STRAT_TABLE)
	{
		for(iter = m_cores.begin(); iter != m_cores.end(); iter++)
		{   
			tempCore = (Core*) *iter;
			if(tempCore == NULL) continue;
			tempCore->getTuple(data, type);
		}
		data += ":";
	} else if (type == SECTION)
	{
		char info[25]; info[0] = 0;
		sprintf(info, "%s,%s,%s,", getSite(), getLeg(), m_name.c_str());
		data += info;	
			
		for(iter = m_cores.begin(); iter != m_cores.end(); iter++)
		{   
			tempCore = (Core*) *iter;
			if(tempCore == NULL) continue;
			tempCore->getTuple(data, type);
		}
		data += ":";
	} else if ((type == SAGAN_TIE) || (type == TIE_SHIFT))
	{	
		for(iter = m_cores.begin(); iter != m_cores.end(); iter++)
		{   
			tempCore = (Core*) *iter;
			if(tempCore == NULL) continue;
			tempCore->getTuple(data, type);
		}
		data += ":";
	} else
	{
		switch(m_type) 
		{
		case GRA :
			coretype ="GRA";
			break;
		case PWAVE :	
			coretype ="Pwave";
			break;
		case SUSCEPTIBILITY :
			coretype ="Susceptibility";
			break;
		case NATURALGAMMA :
			coretype ="Natural Gamma";
			break;
		case REFLECTANCE :
			coretype ="Reflectance";
			break;
		case OTHERTYPE :
			coretype ="Other Type";
			break;
		case ODPOTHER1 :
			coretype ="ODP Other1";
			break;
		case ODPOTHER2 :
			coretype ="ODP Other2";
			break;
		case ODPOTHER3 :
			coretype ="ODP Other3";
			break;
		case ODPOTHER4 :
			coretype ="ODP Other4";
			break;
		case ODPOTHER5 :
			coretype ="ODP Other5";
			break;
		case SPLICE :
			coretype ="Spliced Record";
			break;		
		case USERDEFINEDTYPE :
			coretype = m_annotation;
			break;
		}

		// "154", "926", 0.09, 323.1, 84, 365, "A", 3,
		char info[255]; info[0] = 0;
		sprintf(info, "%s,%s,%s,%.2f,%.2f,%.2f,%.2f,%s,%d,", getSite(), getLeg(),coretype.c_str(), 
			m_range.top, m_range.bottom, m_range.realminvar, m_range.realmaxvar, m_name.c_str(), m_cores.size());

		//cout << info << endl;
		
		data += info;
	
		int i =1;
		char buffer[10];
		for(iter = m_cores.begin(); iter != m_cores.end(); iter++, i++)
		{   
			tempCore = (Core*) *iter;
			if(tempCore == NULL) continue;
			sprintf(buffer, "%d,", tempCore->getNumber());
			data += buffer;
			tempCore->getTuple(data, type);
		}
	} 
	
}

void Hole::setRange( data_range range )
{
	if(m_range.top > range.top)	 // min
	{
		m_range.top = range.top;
	}
	if(m_range.bottom < range.bottom)	// max
	{
		m_range.bottom = range.bottom;
	}

	if(m_range.mindepth > range.mindepth)
	{
		m_range.mindepth = range.mindepth;
	}
	if(m_range.maxdepth < range.maxdepth)
	{
		m_range.maxdepth = range.maxdepth;
	}

	if(m_range.maxdepthdiff < range.maxdepthdiff)
	{
			m_range.maxdepthdiff = range.maxdepthdiff;
	}

	if(m_range.realminvar > range.realminvar)
	{
		m_range.realminvar = range.realminvar;
	}
	if(m_range.realmaxvar < range.realmaxvar)
	{
		m_range.realmaxvar = range.realmaxvar;
	}
	if(m_range.min > range.min)
	{
		m_range.min = range.min;
	}
	if(m_range.max < range.max)
	{
		m_range.max = range.max;
	}	
	//cout << "hole : min=" << m_range.min << " max=" << m_range.max << " " << range.min << " " << range.max << endl;
			
	if(m_range.avedepstep <= 0) 
	{
		m_range.avedepstep = range.avedepstep;
	} else 
	{
		m_range.avedepstep += range.avedepstep;
		m_range.avedepstep /= 2;
	}
	
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
	
	m_updated = true;
}
	
void Hole::setType( int type )
{
        m_type = type;
}

int Hole::getType( void )
{
        return m_type;
}

Core* Hole::createCore( int index )
{
	// check validation with index
	vector<Core*>::iterator iter;
	Core* coreptr= NULL;	
	for(iter = m_cores.begin(); iter != m_cores.end(); iter++) 
	{
		coreptr = (Core*) *iter;	
		if(coreptr->getNumber()  == index) 
		{
#ifdef DEBUG		
			cout << "create : number " <<  coreptr->getNumber() << endl;
#endif
			return NULL;
		}
	}
	
	Core* newCore = new Core(index, this);
	
	for(iter = m_cores.begin(); iter != m_cores.end(); iter++) 
	{
		coreptr = (Core*) *iter;	
		if(coreptr->getNumber()  > index) 
		{
			m_cores.insert(iter, newCore);
			m_updated = true;
			return newCore;
		}
	}
		
	m_cores.push_back(newCore);
	m_updated = true;	
	return newCore;
}

void Hole::deleteCore( int index )
{
	// check validation with index
	vector<Core*>::iterator iter;
	Core* coreptr= NULL;	
	for(iter = m_cores.begin(); iter != m_cores.end(); iter++) 
	{
		coreptr = (Core*) *iter;	
		if (coreptr == NULL) continue;
		
		if(coreptr->getNumber()  == index) 
		{
			m_cores.erase(iter);
			delete coreptr;
			coreptr = NULL;
			//cout << "core is deleted  " <<  index << endl;
			return;
		}
	}
}

int Hole::validate( void ) 
{
	vector<Core*>::iterator iter;
	Core* tempCore = NULL;
	for(iter = m_cores.begin(); iter != m_cores.end(); iter++) 
	{
		tempCore = (Core*) *iter;
		if(tempCore->validate() == 0) 
		{
			return 0;
		}
	}
	
	return 1;
}

int Hole::getNumber( void )
{
	return m_number;
}

Core* Hole::getCore( int index )
{
	// check validation with index
	vector<Core*>::iterator iter;
	Core* coreptr= NULL;
	int ncount = 0;
	for(iter = m_cores.begin(); iter != m_cores.end(); iter++) 
	{
		coreptr = (Core*) *iter;
		//if(coreptr->getNumber()  == index) 
		if (ncount == index)
		{
			return (Core*) *iter;
		}
		ncount++;
	}
	
	return NULL;
}

Core* Hole::getCoreByNo( int index )
{
	// check validation with index
	vector<Core*>::iterator iter;
	Core* coreptr= NULL;
	int ncount = 0;
	for(iter = m_cores.begin(); iter != m_cores.end(); iter++) 
	{
		coreptr = (Core*) *iter;
		if(coreptr->getNumber()  == index) 
		{
			return (Core*) *iter;
		}
		ncount++;
	}
	
	return NULL;
}

Core* Hole::getCore( double basedepth, double offset )
{
	vector<Core*>::iterator iter;
	Core* coreptr= NULL;
	data_range* range;
	double max = basedepth + offset;
	double premax = 9999.0;
	Core* prev_coreptr= NULL;
	bool found = false;
	if(m_cores.size() > 0)
	{
		coreptr = (Core*)m_cores[0]; 
		range = coreptr->getRange();
		if(range->mindepth > basedepth)
			return coreptr;
	}
	
	for(iter = m_cores.begin(); iter != m_cores.end(); iter++) 
	{
		coreptr = (Core*) *iter;
		range = coreptr->getRange();
		//cout << range->mindepth << " " << range->maxdepth << " : " << basedepth << " " << max  << " : " <<  coreptr->getNumber() << endl;
		if((range->mindepth <= basedepth) && (range->maxdepth >= basedepth)) 
		{
			if (found == false) 
			{
				found = true;
				premax = range->maxdepth;
				prev_coreptr = coreptr;		
				continue;		
			} else 
			{
				return coreptr;
			}
		}
		//cout << premax << " " << basedepth << " " << range->mindepth  << " " << max<< endl;
		if((premax <= basedepth) && (range->mindepth >= basedepth)) 
		{
			return prev_coreptr;
		}
		if ((found == true) && (range->mindepth > basedepth)) 
		{
			return prev_coreptr;
		}
		premax = range->maxdepth;
		prev_coreptr = coreptr;
	}
	return NULL;
}

int	Hole::getNumOfCores( void )
{
	int size = m_cores.size();
	return size;
}

void Hole::setName( char* name )
{
	m_name = name;
}

const char* Hole::getName( void )
{
	return m_name.c_str();
}

const char* Hole::getSite( void )
{
	if(m_parent) 
	{
		return m_parent->getSite();
	}
	return NULL;
}

const char*	Hole::getLeg( void )
{
	if(m_parent) 
	{
		return m_parent->getLeg();	
	}
	return NULL;
}

void Hole::setDataFormat( int format )
{
	m_dataFormat = format;
}

int	Hole::getDataFormat( void )
{
	return m_dataFormat;
}

void Hole::setTopAvailable( bool status )
{
	m_topAvailable = status;
}

bool Hole::getTopAvailable( void )
{
	return m_topAvailable;
}	

int Hole::check(char* leg, char* site , char* holename , int corenumber,  char* section)
{
	char* name_ptr = (char*) m_name.c_str();
	
	if(strcmp(name_ptr, holename) == 0)
	{
		return check(leg, site);
	}
	return 0;
}

void Hole::setELDStatus( bool status )
{
	m_eldStatus = status;
}

bool Hole::getELDStatus( void )
{
	return m_eldStatus;
}	

#ifdef DEBUG
void Hole::debugPrintOut( void )
{
	cout << "[Hole] name : " << m_name << "  index : " << m_number << "  number of cores : " << m_cores.size() << endl;
	cout << "[Hole] top : " << m_range.top << "  bottom : " << m_range.bottom  <<  "  min depth : " << m_range.mindepth << "  max depth : " << m_range.maxdepth << endl;
	cout << "[Hole] real min : " << m_range.realminvar << "  real max : " << m_range.realmaxvar <<  "  ave depth : " << m_range.avedepstep << "  mbsf/mcd : " << m_range.ratio <<endl;

	vector<Core*>::iterator iter;
	Core* coreptr = NULL;	
	for(iter = m_cores.begin(); iter != m_cores.end(); iter++) 
	{
		coreptr = (Core*) *iter;	
		coreptr->debugPrintOut();
	}	
}
#endif
