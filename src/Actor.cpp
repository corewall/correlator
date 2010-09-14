//////////////////////////////////////////////////////////////////////////////////
// CorrelatorLib - Correlator Class Library.  
//
// Module   :  Actor.cpp
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

#include <Actor.h>

using namespace std;

int Actor::m_noOfObject =0;

Actor::Actor( void ) :
  m_datatype (VALUE), m_id(m_noOfObject), m_enable(false), m_annotation(""), m_coretype(-1)
{
	m_noOfObject++;
}

Actor::~Actor( void )
{
}

void Actor::setDataType( int type )
{
	m_datatype = type;
}

int Actor::getDataType( void )
{
	return m_datatype;
}

void Actor::setCoreType( int type )
{
	m_coretype = type;
}

int	Actor::getCoreType( void )
{
	return m_coretype;
}

void Actor::setAnnotation( std::string annot )
{
	m_annotation = annot;
	size_t pos = m_annotation.find("All ");
	if (pos !=string::npos)
	{
		pos = pos + 4; 
		m_annotation = m_annotation.substr(pos);
	}
}

const char* Actor::getAnnotation( void )
{
	return m_annotation.c_str();
}	
	
void Actor::setEnable( bool enable )
{
	m_enable = enable;
}

bool Actor::getEnable( void )
{
	return m_enable;
}
