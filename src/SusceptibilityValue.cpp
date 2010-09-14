//////////////////////////////////////////////////////////////////////////////////
// CorrelatorLib - Correlator Class Library.  
//
// Module   :  SusceptibilityValue.cpp
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

#include <SusceptibilityValue.h>
#include <Actor.h>

#ifdef DEBUG
#include <iostream>
#endif

using namespace std;

SusceptibilityValue::SusceptibilityValue( int index, CoreObject* parent ) :
  m_observed(0.0f), m_corrected(0.0f),
  Value(index, parent)  
{
	m_valuetype = SUSCEPTIBILITY;
}

SusceptibilityValue::~SusceptibilityValue( void )
{
	reset();
}


void SusceptibilityValue::reset( void )
{
	m_observed = 0.0f;
	m_corrected = 0.0f;
}

void SusceptibilityValue::copy( Value* valueptr )
{
	SusceptibilityValue* nestvalueptr = (SusceptibilityValue*) valueptr;

	m_observed = nestvalueptr->m_observed;
	m_corrected = nestvalueptr->m_corrected;

	Value::copy(valueptr);
}


void SusceptibilityValue::accept( Actor* flt )
{
	if(flt) 
	{
		flt->visitor(this);
	}
} 

void SusceptibilityValue::setObserve( double value )
{
	m_observed = value;
}

double SusceptibilityValue::getObserve( void )
{
	return m_observed;
}
	
void SusceptibilityValue::setCorrect( double value )
{
	m_corrected = value;
	setRawData(m_corrected);
}

double SusceptibilityValue::getCorrect( void )
{
	return m_corrected;
}

#ifdef DEBUG
void SusceptibilityValue::debugPrintOut( void )
{
	cout << "[SusceptibilityValue] observed : " << m_observed << "  corrected : " << m_corrected << endl;
	Value::debugPrintOut();
}
#endif
