//////////////////////////////////////////////////////////////////////////////////
// CorrelatorLib - Correlator Class Library.  
//
// Module   :  GrapeValue.cpp
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

#include <GrapeValue.h>
#include <Actor.h>

#ifdef DEBUG
#include <iostream>
#endif

using namespace std;

GrapeValue::GrapeValue( int index, CoreObject* parent ) :
  m_density(0.0f), m_corrDensity(0.0f),
  m_gammaCount(0),
  Value(index, parent)
{
	m_valuetype = GRAPE;
}

GrapeValue::~GrapeValue( void )
{
	reset();
}

void GrapeValue::reset( void )
{
	m_density = 0.0f;
	m_corrDensity = 0.0f;
	
	m_gammaCount = 0;
}

void GrapeValue::copy( Value* valueptr )
{
	GrapeValue* nestvalueptr = (GrapeValue*) valueptr;
	m_density = nestvalueptr->m_density;
	m_corrDensity = nestvalueptr->m_corrDensity;
	m_gammaCount = nestvalueptr->m_gammaCount;
	
	Value::copy(valueptr);
}

void GrapeValue::accept( Actor* flt )
{
	if(flt) 
	{
		flt->visitor(this);
	}
} 

void GrapeValue::setDensity( double density )
{
	m_density = density;	
	setRawData(m_density);
}

double GrapeValue::getDensity( void )
{
	return m_density;
}
	
void GrapeValue::setCorrDensity( double density )
{
	m_corrDensity = density;
}

double GrapeValue::getCorrDensity( void )
{
	return m_corrDensity;
}
	
void GrapeValue::setGammaCount( int count )
{
	m_gammaCount = count;
}

int GrapeValue::getGammaCount( void )
{
	return m_gammaCount;
}

#ifdef DEBUG
void GrapeValue::debugPrintOut( void )
{
	cout << "[GrapeValue] density : " << m_density << "  corr density : " << m_corrDensity << "  gamma count : " << m_gammaCount << endl;
	Value::debugPrintOut();
}
#endif
