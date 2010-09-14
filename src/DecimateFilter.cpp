//////////////////////////////////////////////////////////////////////////////////
// CorrelatorLib - Correlator Class Library.  
//
// Module   :  DecimateFilter.cpp
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

#include <CoreTypes.h>
#include <DecimateFilter.h>
#include <Value.h>

#ifdef DEBUG
#include <iostream>
#endif

using namespace std;

DecimateFilter::DecimateFilter( int number )
: m_deciNumber(number)
{
	m_datatype = VALUE;
	
#ifdef DEBUG
	//cout << "[DecimateFilter] decimate number " << m_deciNumber << endl;
#endif	
}

DecimateFilter::~DecimateFilter( void )
{
}

void DecimateFilter::init( void )
{
	m_deciNumber = 1;
	m_enable =false;
}


void DecimateFilter::visitor( CoreObject* object )
{
	if(m_enable == false) return;

	Value* valueptr = (Value*) object;
	int quality = valueptr->getQuality();
	
	if(quality & DECIMATED) 
	{
		quality = quality ^ DECIMATED;
	}
	int index = valueptr->getNumber();
	if((index % m_deciNumber) != 0)
	{
		quality = quality | DECIMATED;
	}
	valueptr->setQuality(quality);
}

void DecimateFilter::setNumber( int number )
{
	m_deciNumber = number;
}

int DecimateFilter::getNumber( void )
{
	return m_deciNumber;
}
