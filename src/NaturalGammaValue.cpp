//////////////////////////////////////////////////////////////////////////////////
// CorrelatorLib - Correlator Class Library.   
//
// Module   :  NaturalGammaValue.cpp
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

#include <NaturalGammaValue.h>
#include <Actor.h>

#ifdef DEBUG
#include <iostream>
#endif

using namespace std;

NaturalGammaValue::NaturalGammaValue( int index, CoreObject* parent ) :
  m_totalCount(0.0f), m_sampleTime(0),
  Value(index, parent)
{
	for(int i=0; i < 5; i++) 
	{
		m_segCount[i] = 0.0f;
	}
	m_valuetype = NATURALGAMMA;
}

NaturalGammaValue::~NaturalGammaValue( void )
{
	reset();
}


void NaturalGammaValue::reset( void )
{
	m_totalCount = 0.0f;
	
	m_sampleTime = 0;
	for(int i=0; i < 5; i++) 
	{
		m_segCount[i] = 0.0f;
	}
}

void NaturalGammaValue::copy( Value* valueptr )
{
	NaturalGammaValue* nestvalueptr = (NaturalGammaValue*) valueptr;

	m_totalCount = nestvalueptr->m_totalCount;
	m_sampleTime = nestvalueptr->m_sampleTime;
	for(int i=0; i < 5; i++) 
	{
		m_segCount[i] = nestvalueptr->m_segCount[i];
	}
	
	Value::copy(valueptr);
}

void NaturalGammaValue::accept( Actor* flt )
{
	if(flt) 
	{
		flt->visitor(this);
	}
} 

void NaturalGammaValue::setTotalCount( double count )
{
	m_totalCount = count;
	setRawData(m_totalCount);		
}

double NaturalGammaValue::getTotalCount( void )
{
	return m_totalCount;
}

void NaturalGammaValue::setSampleTime( int time )
{
	m_sampleTime = time;
}

int NaturalGammaValue::getSampleTime( void )
{
	return m_sampleTime;
}

void NaturalGammaValue::setSegCount( int index, double count )
{
	m_segCount[index] = count;
}

double NaturalGammaValue::getSegCount( int index )
{
	return m_segCount[index];
}	

#ifdef DEBUG
void NaturalGammaValue::debugPrintOut( void )
{
	cout << "[NaturalGammaValue] total count : " << m_totalCount << "  sample time : " << m_sampleTime << endl;
	cout << " seg count : ";
	for(int i=0; i < 5; i++) 
	{
		cout << m_segCount[i] << "  ";
	}
	
	cout << endl;
	Value::debugPrintOut();
}
#endif
