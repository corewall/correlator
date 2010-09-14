//////////////////////////////////////////////////////////////////////////////////
// CorrelatorLib - Correlator Class Library.   
//
// Module   :  Strat.cpp
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

#include <Strat.h>
#include <Core.h>
#include <Actor.h>

#ifdef DEBUG
#include <iostream>
#endif

using namespace std;

// [ Top_P._Lacunosa	N1	0.46	0.46	
// 154	926	A	3	H	1	120	14.70	
// 154	926	A	3	H	2	40	15.40]
// ==> [ name, code, topage, botage, 
// topleg, topsite, tophole topcore, topcoretype, topsection topinterval, topmbsf
// botleg, botsite, bothole, botcore, botcoretype, botsection, botinterval, botmbsf]

Strat::Strat( char* name, char* code, double topage, double botage )
: m_dataType(DIATOMS), m_sedrate(1.0f), m_order(-1)
{
	if(name != NULL) 
	{
		m_name = name; 
	}
	if(code != NULL)
	{
		m_code =code;
	}
	m_age[0] = topage;
	m_age[1] = botage;
	
	m_core[0] = NULL;
	m_core[1] = NULL;
}

Strat::Strat( void )
: m_dataType(DIATOMS), m_order(-1)
{
	m_core[0] = NULL;
	m_core[1] = NULL;
}

Strat::~Strat( void )
{
}

void Strat::accept( Actor* flt )
{
	if(flt->getDataType() == STRAT) 
	{
		flt->visitor(this);
	}
} 

void Strat::update( void )
{
	if(m_updated == true)
	{
		// to do 
		// find value, update mbsf avalue
		m_updated = false;
	}
}
	
Strat* Strat::clone( void )
{
	Strat* cloned = new Strat();
	cloned->m_name = m_name;
	cloned->m_code = m_code;
	
	cloned->m_age[0] = m_age[0];
	cloned->m_age[1] = m_age[1];

	cloned->m_connectedCoreId[0] = m_connectedCoreId[0];
	cloned->m_connectedCoreId[1] = m_connectedCoreId[1];	

	cloned->m_valuetype[0] = m_valuetype[0];
	cloned->m_valuetype[1] = m_valuetype[1];	

	strcpy(cloned->m_section[0], m_section[0]);
	strcpy(cloned->m_section[1], m_section[1]);
	
	cloned->m_interval[0] = m_interval[0];
	cloned->m_interval[1] = m_interval[1];	

	cloned->m_mbsf[0] = m_mbsf[0];
	cloned->m_mbsf[1] = m_mbsf[1];	
	cloned->m_rawmbsf[0] = m_rawmbsf[0];
	cloned->m_rawmbsf[1] = m_rawmbsf[1];	
	
	cloned->m_sedrate = m_sedrate;
	
	cloned->m_dataType = m_dataType;

	
	return cloned;
}
	
double	Strat::calcSedRate( Strat* nextStrat )
{
	if(nextStrat == NULL) return 0;

	m_sedrate = (nextStrat->m_mbsf[1] - m_mbsf[1]) / (nextStrat->m_age - m_age);

	return m_sedrate;

	// find sedrate and average sedrate
	// sedrate = next mcd - current mcd / next age - current age
	// 
	// total
	// total / cnt
	
}		

void Strat::setOrder(int order)
{
	m_order = order;
}

int	Strat::getOrder( void )
{ 
	return m_order;
}
	
void Strat::setTopCore( Core* coreptr )
{
	m_core[0] = coreptr;
}

void Strat::setBotCore( Core* coreptr )	
{
	m_core[1] = coreptr;
}	

const char* Strat::getHoleName( void )
{
	if(m_core[0] != NULL)
	{
		return m_core[0]->getName();
	}
	return NULL;
}

int Strat::applyTopAffine( double offset )
{	
	m_mbsf[0] = m_rawmbsf[0] + offset;
	if(m_connectedCoreId[0] == m_connectedCoreId[1])
	{
		m_mbsf[1] = m_rawmbsf[1] + offset;
	}
	return 1;
}

int Strat::applyBotAffine( double offset )
{	
	m_mbsf[1] = m_rawmbsf[1] + offset;
	return 1;
}

const char* Strat::getDatumName(void)
{
	return m_name.c_str();
}

const char* Strat::getCode(void)
{
	return m_code.c_str();
}

void Strat::setDataType( int type )
{
	m_dataType = type; 
}

int	Strat::getDataType( void )
{
	return m_dataType;
}

void Strat::setTopType( char type )
{
	m_valuetype[0] = type;
}

void Strat::setBotType( char type )
{
	m_valuetype[1] = type;
}

char Strat::getTopType( void )
{
	return m_valuetype[0];
}

char Strat::getBotType( void )
{
	return m_valuetype[1];
}

void Strat::setTopSection( char* value )
{
	strcpy(m_section[0], value);
}

void Strat::setBotSection( char* value )
{
	strcpy(m_section[1], value);
}

char* Strat::getTopSection( void )
{
	return &m_section[0][0];
}

char* Strat::getBotSection( void )
{
	return &m_section[1][0];
}

double Strat::getTopAge( void )
{
	return m_age[0];
}

double Strat::getBotAge( void )
{
	return m_age[1];
}
	
void Strat::setTopMbsf( double mbsf ) 
{
	m_rawmbsf[0] = mbsf;
	m_mbsf[0] = mbsf;	
	//m_updated = true;
}

void Strat::setBotMbsf( double mbsf ) 
{
	m_rawmbsf[1] = mbsf;
	m_mbsf[1] = mbsf;	
	//m_updated = true;
}

double Strat::getTopMbsf( void )
{
	return m_rawmbsf[0];
}

double Strat::getBotMbsf( void )
{
	return m_rawmbsf[1];
}

void Strat::setTopInterval( double interval ) 
{
	m_interval[0] = interval;
	//m_updated = true;
}

void Strat::setBotInterval( double interval ) 
{
	m_interval[1] = interval;
	//m_updated = true;
}

void Strat::getTuple( string& data, int type )
{
	char info[75];
	// code, start_depth, stop_depth
	sprintf(info, "%d,%s,%s,%.2f,%.2f,%.2f,%.2f,%.2f,%d,", m_order, m_name.c_str(), m_code.c_str(), m_mbsf[0], m_mbsf[1], m_rawmbsf[0], m_rawmbsf[1], m_age[0], m_dataType);
	data += info;

}


double Strat::getTopInterval( void )
{
	return m_interval[0];
}

double Strat::getBotInterval( void )
{
	return m_interval[1];
}

void Strat::setTopCoreId( int coreid )
{
	m_connectedCoreId[0] = coreid;
}

void Strat::setBotCoreId( int coreid )
{
	m_connectedCoreId[1] = coreid;
}

int Strat::getTopCoreId( void )
{
	return m_connectedCoreId[0];
}

int Strat::getBotCoreId( void )
{
	return m_connectedCoreId[1];
}

int Strat::getTopCoreNumber( void )
{
	return m_core[0]->getNumber();
}

int Strat::getBotCoreNumber( void )
{
	return m_core[1]->getNumber();
}
	
#ifdef DEBUG
void Strat::debugPrintOut( void )
{
	cout << "[Strat] name : " << m_name << "  code : " << m_code << "  top age : " << m_age[0] << "  bottom age : " << m_age[1] << endl;
	cout << "    top type : " << m_valuetype[0] << "  section : " << m_section[0] << "  mbsf : " << m_mbsf[0] << "  interval : " << m_interval[0] << endl;
	cout << " bottom type : " << m_valuetype[0] << "  section : " << m_section[0] << "  mbsf : " << m_mbsf[0] << "  interval : " << m_interval[0] << endl;
}
#endif

