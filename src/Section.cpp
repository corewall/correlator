//////////////////////////////////////////////////////////////////////////////////
// CorrelatorLib - Correlator Class Library.    
//
// Module   :  Session.cpp
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

#include <Section.h>
#include <Core.h>

#include <iostream>

using namespace std;

Section::Section( int index, CoreObject* parent ) :
  m_number(index), m_startValueptr(NULL), m_endValueptr(NULL),
  CoreObject(parent)
{
}

Section::~Section( void )
{
}

void Section::update( void )
{
	if(m_startValueptr != NULL)
	{
		m_range.mindepth = m_startValueptr->getELD();
		//cout << " section " << m_number << " start " <<  m_range.mindepth << endl;
	}
	if(m_endValueptr != NULL)
	{
		m_range.maxdepth = m_endValueptr->getELD();
		//cout << " section " << m_number << " end " <<  m_range.maxdepth << endl;
	}
		
}
 
void Section::getTuple( std::string& data, int type )
{
	Core* parent = (Core*)m_parent;
	if(parent == NULL) return;
	if(m_startValueptr == NULL) return;
	if(m_endValueptr == NULL) return;

	char info[255];	info[0] = 0;
	if(type == SECTION)
	{
		// <leg> <site> <hole> <core> <type> <section> <depth>
		//sprintf(info, "%d,%c,%d,%.2f,", parent->getNumber(), m_startValueptr->getType(), m_number, m_startValueptr->getELD()); 
		//sprintf(info, "%d,%c,%d,%.2f,%.2f,", parent->getNumber(), m_startValueptr->getType(), m_number, m_startValueptr->getELD(), m_endValueptr->getELD());
		sprintf(info, "%d,%c,%d,%.2f,%.2f,%.2f,%.2f,", parent->getNumber(), m_startValueptr->getType(), m_number, m_startValueptr->getELD(), m_endValueptr->getELD(), m_startValueptr->getTop()* 0.01, m_endValueptr->getBottom()* 0.01);
	} else 
	{
		sprintf(info, "%.3f,", m_startValueptr->getELD());
	}
	
	data += info;
}	
 
int Section::getNumber( void )
{
	return m_number;
}

void Section::setStartValue(Value* valueptr)
{
	m_startValueptr = valueptr;
	m_endValueptr = valueptr;
}

void Section::setEndValue(Value* valueptr)
{
	m_endValueptr = valueptr;
}	
