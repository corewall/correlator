//////////////////////////////////////////////////////////////////////////////////
// CorrelatorLib - Correlator Class Library.  
//
// Module   :  GRAValue.cpp
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

#include <GRAValue.h>
#include <Actor.h>

#ifdef DEBUG
#include <iostream>
#endif

using namespace std;

GraValue::GraValue( int index, CoreObject* parent ) :
  m_density(0.0f), m_corrDensity(0.0f),
  m_gammaCount(0),
  Value(index, parent)
{
	m_valuetype = GRA;
}

GraValue::~GraValue( void )
{
	reset();
}

void GraValue::reset( void )
{
	m_density = 0.0f;
	m_corrDensity = 0.0f;
	
	m_gammaCount = 0;
}

void GraValue::copy( Value* valueptr )
{
	GraValue* nestvalueptr = (GraValue*) valueptr;
	m_density = nestvalueptr->m_density;
	m_corrDensity = nestvalueptr->m_corrDensity;
	m_gammaCount = nestvalueptr->m_gammaCount;
	
	Value::copy(valueptr);
}

void GraValue::accept( Actor* flt )
{
	if(flt) 
	{
		flt->visitor(this);
	}
} 

void GraValue::setDensity( double density )
{
	m_density = density;	
	setRawData(m_density);
}

double GraValue::getDensity( void )
{
	return m_density;
}
	
void GraValue::setCorrDensity( double density )
{
	m_corrDensity = density;
}

double GraValue::getCorrDensity( void )
{
	return m_corrDensity;
}
	
void GraValue::setGammaCount( int count )
{
	m_gammaCount = count;
}

int GraValue::getGammaCount( void )
{
	return m_gammaCount;
}

#ifdef DEBUG
void GraValue::debugPrintOut( void )
{
	cout << "[GRAValue] density : " << m_density << "  corr density : " << m_corrDensity << "  gamma count : " << m_gammaCount << endl;
	Value::debugPrintOut();
}
#endif
