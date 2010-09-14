//////////////////////////////////////////////////////////////////////////////////
// CorrelatorLib - Correlator Class Library.  
//
// Module   :  ReflectanceValue.cpp
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

#include <ReflectanceValue.h>
#include <Actor.h>

#ifdef DEBUG
#include <iostream>
#endif

using namespace std;

ReflectanceValue::ReflectanceValue( int index, CoreObject* parent ) :
  m_L(0.0f), 
  m_a(0.0f), m_b(0.0f),
  Value(index, parent)  
{	
	int i;
	for(i=0; i < 7; i++) 
	{
		m_munsellHue[i] = '\0';
	}
	for(i=0; i < 10; i++) 
	{
		m_munsellValue[i] = '\0';
	}
	for(i=0; i < 31; i++) 
	{
		m_nmValue[i] = 0.0f;
	}
	m_valuetype = REFLECTANCE;
}

ReflectanceValue::~ReflectanceValue( void )
{
	reset();
}

void ReflectanceValue::reset( void )
{
	m_L = 0.0f;
	m_a = 0.0f;
	m_b = 0.0f;

	int i;
	for(i=0; i < 7; i++) 
	{
		m_munsellHue[i] = '\0';
	}
	for(i=0; i < 10; i++) 
	{
		m_munsellValue[i] = '\0';
	}
	for(i=0; i < 31; i++) 
	{
		m_nmValue[i] = 0.0f;
	}
}

void ReflectanceValue::copy( Value* valueptr )
{
	ReflectanceValue* nestvalueptr = (ReflectanceValue*) valueptr;

	m_L = nestvalueptr->m_L;
	m_a = nestvalueptr->m_a;
	m_b = nestvalueptr->m_b;
	
	int i;
	for(i=0; i < 7; i++) 
	{
		m_munsellHue[i] = nestvalueptr->m_munsellHue[i];
	}
	for(i=0; i < 10; i++) 
	{
		m_munsellValue[i] = nestvalueptr->m_munsellValue[i];
	}
	for(i=0; i < 31; i++) 
	{
		m_nmValue[i] = nestvalueptr->m_nmValue[i];
	}	
	Value::copy(valueptr);
}

void ReflectanceValue::accept( Actor* flt )
{
	if(flt) 
	{
		flt->visitor(this);
	}
} 

void ReflectanceValue::setL( double value )
{
	m_L = value;	
}

double ReflectanceValue::getL( void )
{
	return m_L;
}
	

void ReflectanceValue::seta( double value )
{
	m_a = value;	
}

double ReflectanceValue::geta( void )
{
	return m_a;
}

void ReflectanceValue::setb( double value )
{
	m_b = value;	
}

double ReflectanceValue::getb( void )
{
	return m_b;
}

void ReflectanceValue::setHue( char* hue )
{
	for(int i=0; i < 7; i++) 
	{
		m_munsellHue[i] = hue[i];
	}
}

char* ReflectanceValue::getHue( void )
{
	return &m_munsellHue[0]; 
}

void ReflectanceValue::setValue( char* value )
{
	for(int i=0; i < 10; i++) 
	{
		m_munsellValue[i] = value[i];
	}
}

char* ReflectanceValue::getValue( void )
{
	return &m_munsellValue[0];
}
	
void ReflectanceValue::setValue( int index, double value )
{
	m_nmValue[index] = value;
	if(index == 15) 
	{
		setRawData(m_nmValue[15]);		
	}			
}

double ReflectanceValue::getValue( int index )
{
	return m_nmValue[index];
}

#ifdef DEBUG
void ReflectanceValue::debugPrintOut( void )
{
	cout << "[ReflectanceValue] L : " << m_L << "  a : " << m_a << "  b : " << m_b  << endl;
	cout << " Hue : " << m_munsellHue << " Value : " << m_munsellValue << endl;
	cout << " mnValue : " << m_nmValue[0];
	for(int i=1; i < 31; i++) 
	{
		cout << " " << m_nmValue[i];
		if((i % 5) == 0) 
		{
			cout << endl;
		}
	}
	
	cout << endl;
	Value::debugPrintOut();
}
#endif
