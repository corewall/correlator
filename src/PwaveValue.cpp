//////////////////////////////////////////////////////////////////////////////////
// CorrelatorLib - Correlator Class Library.   
//
// Module   :  PwaveValue.cpp
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

#include <PwaveValue.h>
#include <Actor.h>

#ifdef DEBUG
#include <iostream>
#endif

using namespace std;

PwaveValue::PwaveValue( int index, CoreObject* parent ) :
  m_velocity(0.0f), m_sigStrength(0),
  m_travelTime(0), m_displacement(0),
  Value(index, parent)  
{
	m_valuetype = PWAVE;
}

PwaveValue::~PwaveValue( void )
{
	reset();
}

void PwaveValue::reset( void )
{
	m_velocity = 0.0f;
	
	m_sigStrength = 0;
	m_travelTime = 0;
	m_displacement = 0;
}

void PwaveValue::copy( Value* valueptr )
{
	PwaveValue* nestvalueptr = (PwaveValue*) valueptr;

	m_velocity = nestvalueptr->m_velocity;
	m_sigStrength = nestvalueptr->m_sigStrength;
	m_travelTime = nestvalueptr->m_travelTime;
	m_displacement = nestvalueptr->m_displacement;
	
	Value::copy(valueptr);
}

void PwaveValue::accept( Actor* flt )
{
	if(flt) 
	{
		flt->visitor(this);
	}
} 

void PwaveValue:: setVelocity( double velocity )
{
	m_velocity = velocity;
	setRawData(m_velocity);
}

double PwaveValue::getVelocity( void )
{
	return m_velocity;
}
	
void PwaveValue::setStrength( int strenth )
{
	m_sigStrength = strenth;
}

int PwaveValue::getStrength( void )
{
	return m_sigStrength;
}
	
void PwaveValue::setTravelTime( int time )
{
	m_travelTime = time;
}

int PwaveValue::getTravelTime( void )
{
	return m_travelTime;
}

void PwaveValue::setDisplacement( int value )
{
	m_displacement = value;
}

int PwaveValue::getDisplacement( void )
{
	return m_displacement;
}


#ifdef DEBUG
void PwaveValue::debugPrintOut( void )
{
	cout << "[PwaveValue] velocity : " << m_velocity << "  signal strength : " << m_sigStrength << "  travel time : " << m_travelTime << "  displacement : " << m_travelTime << endl;
	Value::debugPrintOut();
}
#endif
