//////////////////////////////////////////////////////////////////////////////////
// CorrelatorLib - Correlator Class Library.  
//
// Module   :  Data.cpp
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

#include <Data.h>
#include <Actor.h>

#ifdef DEBUG
#include <iostream>
#endif

using namespace std;

Data::Data( void ) :
  m_site (""), m_leg(""), 
  m_subleg(-1), m_type(-1),
  m_dataFormat(-1), m_flip(NO),
  m_corr_status(NO), m_affine_status(NO),
  m_stretch(100.0f), m_mudline(0.0f)
{
}

Data::~Data( void )
{
	reset();
}

void Data::init( int type, bool fromFile )
{
	m_stretch = 100.0f;
	m_mudline = 0.0f;
	m_range.ratio = -1.0;
 	m_range.min = 9999.0;
	m_range.max = -9999.0;
	
	vector<Hole*>::iterator iter;
	Hole* tempHole = NULL;
	for(iter = m_holes.begin(); iter != m_holes.end(); iter++)
	{
			tempHole = (Hole*) *iter;
			if(tempHole)
			{
					tempHole->init(type, fromFile);
			}
	}
	m_updated = true;

#ifdef DEBUG
        cout << "[Data] initialized : ";
	if(type == ALL_TIE) 
	{
		cout << "COMPOSITED_TIE and REAL_TIE" << endl;
	} else if(type == COMPOSITED_TIE) 
	{
		cout << "COMPOSITED_TIE" << endl;
	} else if(type == REAL_TIE) 
	{
		cout << "REAL_TIE" << endl;
	}	
#endif 
}

void Data::init( int type, int coretype, char* annotation, bool fromFile )
{
	vector<Hole*>::iterator iter;
	m_range.ratio = -1.0;
	Hole* tempHole = NULL;
 	m_range.min = 9999.0;
	m_range.max = -9999.0;	
	for(iter = m_holes.begin(); iter != m_holes.end(); iter++)
	{
			tempHole = (Hole*) *iter;
			if(tempHole)
			{
					tempHole->init(type, coretype, annotation, fromFile);
			}
	}
	m_updated = true;	
}
	
void Data::reset( void )
{
	m_range.ratio = -1.0;
	// delete holes
	vector<Hole*>::iterator iter;
	Hole* tempHole = NULL;
	for(iter = m_holes.begin(); iter != m_holes.end(); iter++) 
	{
		tempHole = (Hole*) *iter;
		if(tempHole) 
		{
			delete tempHole;
			tempHole = NULL;
		}
	}
	m_holes.clear();
}

void Data::reset( int type, int coretype, char* annotation )
{
	m_range.ratio = -1.0;
	vector<Hole*>::iterator iter;
	Hole* tempHole = NULL;
	for(iter = m_holes.begin(); iter != m_holes.end(); iter++) 
	{
		tempHole = (Hole*) *iter;
		if(tempHole == NULL) continue;
		
		if(coretype != USERDEFINEDTYPE)
		{	
			if(tempHole->getType() == coretype)
			{
				tempHole->reset(type);
			}
		} else 
		{
			if(strcmp(tempHole->getAnnotation(), annotation) ==0)
			{
				tempHole->reset(type);
			}
		}
	}
}

void Data::accept( Actor* flt )
{
	if(flt->getDataType() == DATA) 
	{
		flt->visitor(this);
	} else 
	{
		vector<Hole*>::iterator iter;
		Hole* tempHole = NULL;
		for(iter = m_holes.begin(); iter != m_holes.end(); iter++) 
		{
			tempHole = (Hole*) *iter;
			tempHole->accept(flt);
		}
	}
} 

void Data::update( void )
{
	vector<Hole*>::iterator iter;
	Hole* tempHole = NULL;
	for(iter = m_holes.begin(); iter != m_holes.end(); iter++) 
	{
		tempHole = (Hole*) *iter;
		if(tempHole == NULL) continue;
		tempHole->update();
	}
	if(m_updated == true)
	{
		// to do 
		updateRange();
		m_updated = false;
	}
} 

void Data::getTypeRange(  int type, char* annot, double& min, double& max )
{
	double temp_min, temp_max;
	min= 9999.99;
	max=-9999.99;
	vector<Hole*>::iterator iter;
	Hole* tempHole = NULL;
	for(iter = m_holes.begin(); iter != m_holes.end(); iter++) 
	{
		tempHole = (Hole*) *iter;
		if(tempHole == NULL) continue;
		if (tempHole->getType() == type)
		{
			if ((type == USERDEFINEDTYPE) && (strcmp(tempHole->getAnnotation(), annot) != 0))
				continue;
			temp_min= tempHole->getMin();
			temp_max= tempHole->getMax();
			if (temp_min < min)
			{
				min = temp_min;
			}
			if (temp_max > max)
			{
				max = temp_max;
			}
		}
	}
}
	

void Data::getTuple( string& data, int type ) 
{
	char info[25]; info[0] = 0;
	if((type != STRAT_TABLE) && (type != SECTION) && (type != SAGAN_TIE) && (type!= TIE_SHIFT))
	{
		sprintf(info, "%.2f,%.2f,", m_range.mindepth, m_range.maxdepth);
		data = info;
	}
	
	vector<Hole*>::iterator iter;
	Hole* tempHole = NULL;
	int nIndex = 0;

	for(iter = m_holes.begin(); iter != m_holes.end(); iter++, nIndex++)
	{
		tempHole = (Hole*) *iter;
		if (tempHole == NULL) continue;
		if((type == STRAT_TABLE) || (type == SAGAN_TIE)  || (type == TIE_SHIFT))
		{
			sprintf(info, "%d,", nIndex);
			data += info;
		}
        tempHole->getTuple(data, type);
	}
	data += "#";
}

void Data::setRange( data_range range )
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
	//cout << m_range.ratio << endl;		
	m_updated = true;
}
	
Hole* Data::createHole( int index, char* name, int type, char* annotation )
{
	// check validation with index
	vector<Hole*>::iterator iter, iter_insert;
	Hole* holeptr = NULL;
	for(iter = m_holes.begin(); iter != m_holes.end(); iter++) 
	{
		holeptr = (Hole*) *iter;
		if(holeptr->getNumber()  == index) 
		{
			return NULL;
		}
	}

	char name_char = name[0];	
	
	Hole* newHole = new Hole(index, this);
	newHole->setName(name);
	
	int prevType = -1;
	const char* prevAnnot = NULL;
	const char* name_ptr;
	char name_hole_char;


	for(iter = m_holes.begin(); iter != m_holes.end(); iter++) 
	{
		holeptr = (Hole*) *iter;
		//cout << " hole created type " << holeptr->getType() << " " << type << endl;

		name_ptr = (char*) holeptr->getName();
		name_hole_char = name_ptr[0];

		//cout << "-------- CHECK " << name_hole_char << " " << name_char << " " << holeptr->getType() << " " << type << " " << holeptr->getAnnotation() << " " << annotation << endl;
		if((name_hole_char  >= name_char) && checkType(holeptr->getType(),type, holeptr->getAnnotation(), annotation)) 
		{
			//cout << "------------char " << name_hole_char << " " << name_char << endl;
			m_holes.insert(iter, newHole);
			return newHole;
		}	
		else if(checkType(prevType,type, prevAnnot, annotation) && !checkType(holeptr->getType(), prevType, holeptr->getAnnotation(), prevAnnot))
		{
			//cout << "?????------------char " << name_hole_char << " " << name_char << endl;
			m_holes.insert(iter, newHole);
			return newHole;
		}

		prevType = holeptr->getType();
		prevAnnot = holeptr->getAnnotation();
	}
	m_holes.push_back(newHole);
	return newHole;
}

bool Data::checkType(int typeA, int typeB, const char* annotA, const char* annotB)
{
	if(typeA == USERDEFINEDTYPE)
	{
		if(typeA != typeB) 
			return false;
		if(strcmp(annotA, annotB) == 0)
			return true;
	} else 
	{
		if(typeA == typeB)
			return true;
	}
	return false;
}


void Data::sort( )
{
	/*
	vector<Hole*>::iterator iterA;
	vector<Hole*>::iterator iterB;
	Hole* holeptrA = NULL;
	Hole* holeptrB = NULL;
	for(iterA = m_holes.begin(); iterA != m_holes.end(); iterA++) 
	{
		holeptrA = (Hole*) *iterA;
		iterB = iterA;
		iterB++;
		holeptrB = (Hole*) *iterB;
		if(holeptrA->getName() > holeptrB->getName()) 
		{
			m_holes.erase(iterB);
			m_holes.insert(iterA, holeptrB);
			iterA = m_holes.begin();
		}
	}
	*/
}


Hole* Data::getHole( char* name )
{
	vector<Hole*>::iterator iter;
	Hole* holeptr = NULL;	
	char* name_ptr;
	for(iter = m_holes.begin(); iter != m_holes.end(); iter++) 
	{
		holeptr = (Hole*) *iter;
		name_ptr = (char*) holeptr->getName(); 
		if(strcmp(name_ptr, name) == 0) 
		{
			return (Hole*) *iter;
		}
	}
	
	return NULL;
}

Hole* Data::getHole( char* name, int format, int datatype, char* annotation )
{
	vector<Hole*>::iterator iter;
	Hole* holeptr = NULL;	
	char* name_ptr;
	if(datatype == USERDEFINEDTYPE)
	{
		if(annotation == NULL) return NULL;
		
		for(iter = m_holes.begin(); iter != m_holes.end(); iter++) 
		{
			holeptr = (Hole*) *iter;
			if(m_annotation.find(annotation) != string::npos)
			{
				name_ptr = (char*) holeptr->getName();
				if((strcmp(name_ptr, name) == 0) && (holeptr->getDataFormat() == format) &&  (holeptr->getType() == datatype))
				{
#ifdef DEBUG				
					cout << "found " << endl;
#endif
					return (Hole*) *iter;
				}
			}
		}	
	}
	else 
	{			
		for(iter = m_holes.begin(); iter != m_holes.end(); iter++) 
		{
			holeptr = (Hole*) *iter;
			name_ptr = (char*) holeptr->getName();
			if((strcmp(name_ptr, name) == 0) && (holeptr->getDataFormat() == format) &&  (holeptr->getType() == datatype))
			{
#ifdef DEBUG			
				cout << "found " << endl;
#endif
				return (Hole*) *iter;
			}
		}
	}
	return NULL;
}

Hole* Data::getHole( char* name, int datatype, char* annotation )
{
	vector<Hole*>::iterator iter;
	Hole* holeptr = NULL;	
	char* name_ptr;
	
	if (datatype == -1)
	{
		for(iter = m_holes.begin(); iter != m_holes.end(); iter++) 
		{
			holeptr = (Hole*) *iter;
			if(holeptr == NULL) continue;
			name_ptr = (char*) holeptr->getName();

			if(strcmp(name_ptr, name) == 0) 
			{
				return (Hole*) *iter;
			}
		}	
	} else if(datatype != USERDEFINEDTYPE)
	{
		for(iter = m_holes.begin(); iter != m_holes.end(); iter++) 
		{
			holeptr = (Hole*) *iter;
			if(holeptr == NULL) continue;
			name_ptr = (char*) holeptr->getName();
			if((strcmp(name_ptr, name) == 0) && (holeptr->getType() == datatype))
			{
				return (Hole*) *iter;
			}
		}
	} else
	{
		for(iter = m_holes.begin(); iter != m_holes.end(); iter++) 
		{
			holeptr = (Hole*) *iter;
			if(holeptr == NULL) continue;
			name_ptr = (char*) holeptr->getName();
			if((strcmp(name_ptr, name) == 0) && (holeptr->getType() == datatype) && (strcmp(holeptr->getAnnotation(), annotation) ==0))
			{
				return (Hole*) *iter;
			}
		}
	}
	return NULL;
}
	
Hole* Data::getHole( int index )
{
	// check validation with index
	vector<Hole*>::iterator iter;
	Hole* holeptr = NULL;	
	for(iter = m_holes.begin(); iter != m_holes.end(); iter++) 
	{
		holeptr = (Hole*) *iter;	
		if(holeptr->getNumber()  == index) 
		{
			return (Hole*) *iter;
		}
	}
	
	return NULL;
}

Hole* Data::getHole( char* name, int index )
{
	vector<Hole*>::iterator iter = m_holes.begin();
	Hole* holeptr = NULL;
	int typecount = 0;
	int prevType = -1;
	int type;	
	char* name_ptr;	
	for(iter; iter != m_holes.end(); iter++) 
	{
		holeptr = (Hole*) *iter;	
		if(holeptr == NULL) continue;
		
		type = holeptr->getType();
		if(type != prevType) 
		{
			typecount++;
		}
		prevType = type;

		if (typecount > index) break;
	}
	
	for(iter; iter != m_holes.end(); iter++) 
	{
		holeptr = (Hole*) *iter;
		if(holeptr == NULL) continue;
		
		//cout << "type = " << holeptr->getType() << endl;
		name_ptr = (char*) holeptr->getName();
		if(strcmp(name_ptr, name) == 0) 
		{
			return (Hole*) *iter;
		}
	}
	
	return NULL;
}

int	Data::getNumOfTypes(void)
{
	int typecount = 0;
	int prevType = -1;
	int type;
	vector<Hole*>::iterator iter;
	Hole* holeptr = NULL;	
	for(iter = m_holes.begin(); iter != m_holes.end(); iter++) 
	{
		holeptr = (Hole*) *iter;	
		if(holeptr == NULL) continue;
		
		type = holeptr->getType();
		if(type != prevType) 
		{
			typecount++;
		}
		prevType = type;
	}
	return typecount;
}
	
void Data::remove( int datatype )
{
	vector<Hole*>::iterator iter;
	Hole* holeptr = NULL;	
	//for(iter = m_holes.begin(); iter != m_holes.end(); iter++) 
	iter = m_holes.begin();
	while (iter != m_holes.end())
	{
		holeptr = (Hole*) *iter;	
		if(holeptr == NULL) continue;
		if(holeptr->getType() == datatype)
		{
			delete holeptr;
			holeptr = NULL;
			m_holes.erase(iter);
			iter = m_holes.begin();
			//std::cout << "deleted " << datatype << endl;
		} else 
		{
			iter++;
		}
	}
}

int Data::validate( void ) 
{
	vector<Hole*>::iterator iter;
	Hole* holeptr = NULL;	
	for(iter = m_holes.begin(); iter != m_holes.end(); iter++) 
	{
		holeptr = (Hole*) *iter;	
		if(holeptr->validate() == 0) 
		{
			return 0;
		}

	}
	return 1;
}

int	Data::getNumOfHoles( void )
{
	int size = m_holes.size();
	return size;
}

int	Data::getNumOfHoles( char* name )
{
	int size = 0;
	char* name_ptr;
	vector<Hole*>::iterator iter;
	Hole* holeptr = NULL;	
	for(iter = m_holes.begin(); iter != m_holes.end(); iter++) 
	{
		holeptr = (Hole*) *iter;	
		name_ptr = (char*) holeptr->getName();
		if(strcmp(name_ptr, name) == 0) 
		{
			size++;
		}
	}
	return size;
}

void Data::setStretch( double stretch )
{
	m_stretch = stretch;
}
 
double Data::getStretch( void )
{
	return m_stretch;
}

void Data::setMudLine( double line )
{
	m_mudline = line;
}

double Data::getMudLine( void )
{
	return m_mudline;
}

void Data::setCorrStatus( int status )
{
	m_corr_status = status;
}

int	Data::getCorrStatus( void )
{
	return m_corr_status;
}

void Data::setAffineStatus( int status )
{
	m_affine_status = status;
}

int	Data::getAffineStatus( void )
{
	return m_affine_status;
}

void Data::setSite( char* site )
{
	m_site = site;
}

const char* Data::getSite( void )
{
	return m_site.c_str();
}

void Data::setLeg( char* leg )
{
	m_leg = leg;
}

const char* Data::getLeg( void )
{
	return m_leg.c_str();
}

void Data::setSubLeg( int leg )
{
	m_subleg = leg;
}

int Data::getSubLeg( void )
{
	return m_subleg;
}

void Data::setType( int type )
{
	m_type = type;
}

int	Data::getType( void )
{
	return m_type;
}

void Data::setFlip( int flip )
{
	m_flip = flip;
}

int	Data::isFlip( void )
{
	return m_flip;
}

void Data::setDataFormat( int format )
{
	m_dataFormat = format;
}

int	Data::getDataFormat( void )
{
	return m_dataFormat;
}

int Data::check(char* leg, char* site , char* holename , int corenumber,  char* section)
{
	if((strcmp(m_leg.c_str(), leg) == 0) && (strcmp(m_site.c_str(),site) == 0))
	{
		return 1;
	}
	return 0;
}


#ifdef DEBUG
void Data::debugPrintOut( void )
{
	cout << "[Data] leg : " << m_leg.c_str() << "  site : " << m_site.c_str() << "  type : " << m_type <<  " number of holes : " << m_holes.size();
	switch (m_dataFormat)
	{
	case MST95REPORT:
		 cout << "  format : MST95REPORT " << endl;		
		 break;
	case TKREPORT:
		 cout << "  format : TKREPORT " << endl;		
		break;
	case ODPOTHER:
		 cout << "  format : ODPOTHER " << endl;		
		break;
	case ODPOTHER1:
		 cout << "  format : ODPOTHER1 " << endl;		
		break;
	case ODPOTHER2:
		 cout << "  format : ODPOTHER2 " << endl;		
		break;
	case ODPOTHER3:
		 cout << "  format : ODPOTHER3 " << endl;		
		break;
	case ODPOTHER4:
		 cout << "  format : ODPOTHER4 " << endl;		
		break;
	case ODPOTHER5:
		 cout << "  format : ODPOTHER5 " << endl;		
		break;
	case JANUSCLEAN:
		 cout << "  format : JANUSCLEAN " << endl;		
		break;
	case JANUSORIG:
		 cout << "  format : JANUSORIG " << endl;		
		break;
	default:
		 cout << "  format : not defined " << endl;		
	}
	
	cout << "[Data] top : " << m_range.top << "  bottom : " << m_range.bottom << "  min depth : " << m_range.mindepth << "  max depth : " << m_range.maxdepth << endl;
	cout << "[Data] real min : " << m_range.realminvar << "  real max : " << m_range.realmaxvar  << "  ave depth : " << m_range.avedepstep << "  mbsf/mcd : " << m_range.ratio << endl;

	vector<Hole*>::iterator iter;
	Hole* holeptr = NULL;	
	for(iter = m_holes.begin(); iter != m_holes.end(); iter++) 
	{
		holeptr = (Hole*) *iter;	
		holeptr->debugPrintOut();
	}	
}
#endif
