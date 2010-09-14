//////////////////////////////////////////////////////////////////////////////////
// CorrelatorLib - Correlator Class Library.  
//
// Module   :  CoreObject.cpp
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

#include <CoreObject.h>

unsigned int CoreObject::m_noOfObject =0;

data_range::data_range() : 
top(9999.0f), bottom(-9999.0f), mindepth(9999.0f), 
maxdepth(-9999.0f), min(9999.0f), max(-9999.0f), avedepstep(0.0f),
maxdepthdiff(-9999.0f),
realminvar(9999.0f), realmaxvar(-9999.0f), ratio(-1.0f)
{
}

void data_range::init(void)
{
	top =9999.0f;
	bottom =-9999.0f;
	mindepth =9999.0f;
	maxdepth =-9999.0f;
	min =9999.0f;
	max =-9999.0f;
	avedepstep =0.0f;
	maxdepthdiff =-9999.0f;
	realminvar =9999.0f;
	realmaxvar =-9999.0f;
	ratio =-1.0f;
}

CoreObject::CoreObject( void ) 
: m_id(m_noOfObject), m_timestamp(0.0f),
  m_parent(NULL), m_updated(true),
  m_dataValidation(true),
  m_annotation("")
{
	m_noOfObject++;
}

CoreObject::CoreObject( CoreObject* parent )
: m_id(m_noOfObject),  m_timestamp(0.0f),
  m_parent(parent), m_updated(false),
  m_dataValidation(true),
  m_annotation("") 
{
	m_noOfObject++;
}


CoreObject::~CoreObject( void )
{
}


void CoreObject::copyRange( CoreObject* objectptr )
{
	//m_id(m_noOfObject), 
	m_timestamp = objectptr->m_timestamp;
	m_parent = objectptr->m_parent;
	m_dataValidation = objectptr->m_dataValidation;
	m_annotation = objectptr->m_annotation;

	m_range.top = objectptr->m_range.top;
	m_range.bottom = objectptr->m_range.bottom;
	m_range.mindepth = objectptr->m_range.mindepth;
	m_range.maxdepth = objectptr->m_range.maxdepth;
	m_range.min = objectptr->m_range.min;
	m_range.max = objectptr->m_range.max;
	m_range.realminvar = objectptr->m_range.realminvar;
	m_range.realmaxvar = objectptr->m_range.realmaxvar;
	m_range.ratio = objectptr->m_range.ratio;
	m_range.avedepstep = objectptr->m_range.avedepstep;
}

void CoreObject::updateRange( void )
{
	if(m_parent)
	{
		m_parent->setRange(m_range);
	}
}

void CoreObject::setRange( void )
{
	m_range.min = 9999.0;
    m_range.max = -9999.0;
    m_range.realminvar = m_range.min;
    m_range.realmaxvar = m_range.max;
	if(m_parent)
	{
		m_parent->setRange();
	}
}

void CoreObject::initRange( void )
{
	m_range.init();
}


void CoreObject::setTop( double top ) 
{ 
	m_range.top = top; 
	m_range.bottom = top;
}

unsigned int CoreObject::getId( void )
{
	return m_id;
}

void CoreObject::setId(unsigned int nId)
{
	m_id = nId;
}

void CoreObject::setParent( CoreObject* parent )
{
	m_parent = parent;
}

CoreObject* CoreObject::getParent( void )
{
	return m_parent;
}

void CoreObject::setUpdate( void )
{
	m_updated = true;
}

void CoreObject::setAnnotation( char* annotation )
{
	m_annotation = annotation;
}

const char* CoreObject::getAnnotation( void )
{
	return m_annotation.c_str();
}
