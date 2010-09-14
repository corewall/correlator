//////////////////////////////////////////////////////////////////////////////////
// CorrelatorLib - Correlator Class Library.  
//
// Module   :  Value.cpp
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

#include <math.h>

#include <Value.h>
#include <Actor.h>
#include <Core.h>

#ifdef DEBUG
#include <iostream>
#endif

using namespace std;

Value::Value( int index, CoreObject* parent ) :
  m_number(index), m_runNumber(0), m_source(NULL),
  m_valuetype(OTHERTYPE), m_type('\0'), 
  m_depth(0.0f), m_stretch(100.0f), m_offset(0.0f),
  m_quality(GOOD), m_otherodp(0.0f),  
  m_mbsf(0.0f), m_eld(0.0f), m_mcd(0.0f),
  m_smoothStatus(NONE), m_mcd_splicer(0.0f), m_stretched_mcd(0.0f),
  m_affine_status(NO), m_corr_status(NO), 
  m_manual_corr_status(NO), m_sectionId(-1), m_cull_tabled(false),
  CoreObject(parent)
{
	m_data[0] = 0.0f;
	m_data[1] = 0.0f;
	m_rate = 1.0f;
	m_b = 0.0f;
	m_shiftb = 0.0f;
	memset(m_section, 0, 2);
}

Value::~Value( void )
{
	reset();
}

void Value::init( int type )
{
	// initialize data
	// todo
	if(type == QUALITY)
	{
		m_data[1] = m_data[0];
		m_quality = GOOD;
		m_smoothStatus =NONE;
		setDepth(m_mbsf);
		m_range.min = 9999.0;
		m_range.max = -9999.0;
		if(m_data[0]  > m_range.max)
				m_range.max = m_data[0];
		if(m_data[0] < m_range.min)
				m_range.min = m_data[0];

		if(fabs(m_data[0] - BAD_CODE) <= 1)
		{
			m_quality=BAD_SB_DEPTH;
		} 
	}
	else if (type ==QUALITY_SPLICE)
	{
		m_data[1] = m_data[0];
		m_quality = GOOD;
		m_smoothStatus =NONE;
		if(fabs(m_data[0] - BAD_CODE) <= 1)
		{
			m_quality=BAD_SB_DEPTH;
		} 		
	}
	else  {
		//m_data[1] = m_data[0];
		m_quality = GOOD;
		m_mbsf = m_depth;
		m_mcd = m_depth;
		m_eld = m_depth;
		m_mcd_splicer = m_depth;
		m_stretched_mcd = m_depth;		
		m_rate = 1.0f;
		m_b = 0.0f;
		m_shiftb = 0.0f;
		m_stretch = 100.0f;
		//m_offset = 0.0f;
		m_range.min = 9999.0;
		m_range.max = -9999.0;
			
		m_updated = true;		
		m_corr_status = m_manual_corr_status = NO;
		//std::cout << "depth = " << m_mbsf << " , " << m_mcd << std::endl;

	}

}

void Value::initShift( void )
{
	m_shiftb = 0.0f;
	m_rate = 1.0f;
	m_b = 0.0f;	
	m_updated = true;
	update();	
}

void Value::reset( void )
{
	m_data[0] = 0.0f;
	m_data[1] = 0.0f;
	m_rate = 1.0f;
	m_b = 0.0f;
	m_shiftb = 0.0f;
	m_offset = 0.0f;

	memset(m_section, 0, 2);

	m_type = '\0';
	m_quality = GOOD;
	
	m_runNumber = 0;
	
	m_otherodp = 0.0f;
	m_depth = 0.0f;
	m_mbsf = 0.0f;
	m_mcd = 0.0f;
	m_eld = 0.0f;
	m_mcd_splicer = 0.0f;
	m_stretched_mcd = 0.0f;	
}

void Value::reset( int type )
{
	//if (type == BAD_CULLTABLE)
	//{
		m_cull_tabled = false;
		CoreObject::setRange();
		m_updated = true;		
	//}
}

void Value::copy( CoreObject* objectptr )
{
	Value* valueptr = (Value*) objectptr;
	
	m_data[0] = valueptr->m_data[0];
	m_data[1] = valueptr->m_data[1];

	strcpy(m_section, valueptr->m_section);
	m_sectionId = valueptr->m_sectionId;

	m_type = valueptr->m_type;
	m_source = valueptr->m_source;
	//m_quality = valueptr->m_quality;
	m_valuetype = valueptr->m_valuetype;
	m_runNumber = valueptr->m_runNumber;
	
	m_otherodp = valueptr->m_otherodp;
	m_depth = valueptr->m_depth;
	m_mbsf = valueptr->m_mbsf;
	m_mcd = valueptr->m_mcd;
	m_eld = valueptr->m_eld;	
	m_mcd_splicer = valueptr->m_mcd_splicer;
	m_stretch =  valueptr->m_stretch;
	m_rate = valueptr->m_rate;
	m_b = valueptr->m_b;
	m_shiftb = valueptr->m_shiftb;
	m_affine_status = valueptr->m_affine_status;
	m_corr_status = valueptr->m_corr_status;
	m_manual_corr_status = valueptr->m_manual_corr_status;
	m_range.top = valueptr->m_range.top;
	m_range.bottom = valueptr->m_range.bottom;
	m_range.mindepth = valueptr->m_range.mindepth;
	m_range.maxdepth = valueptr->m_range.maxdepth;
	m_range.min = valueptr->m_range.min;
	m_range.max = valueptr->m_range.max;
	m_range.realminvar = valueptr->m_range.realminvar;
	m_range.realmaxvar = valueptr->m_range.realmaxvar;
	m_range.ratio = valueptr->m_range.ratio;
	m_range.avedepstep = valueptr->m_range.avedepstep;
	m_offset = valueptr->m_offset;
	m_stretched_mcd = valueptr->m_stretched_mcd;
	m_updated = true;
}

void Value::copyData( CoreObject* objectptr )
{
	if (objectptr == NULL) return;
	Value* valueptr = (Value*) objectptr;
	m_data[0] = valueptr->m_data[0];
	m_data[1] = valueptr->m_data[1];
	//cout << "data " << m_data[0] << " " << m_data[1] << endl;
}

void Value::accept( Actor* flt )
{
	if(flt->getDataType() == VALUE) 
	{
		flt->visitor(this);
	}
} 

void Value::update( void )
{
	if(m_updated == true)
	{
		m_updated = false;

		if(m_quality & BAD_SB_DEPTH) 
		{			
			return;
		}
		if (m_cull_tabled == true)
		{
			return;
		}
		
		m_range.ratio = m_mbsf / m_mcd;	
		
		m_mcd = m_mbsf + m_offset;	

		if(m_corr_status == YES)
		{
			double rate = m_stretch / 100.0f;
			m_eld =  m_mcd * rate;	
			if(m_affine_status == YES)
			{
				m_mcd += m_shiftb;
			} else 
			{
				m_mcd = m_mbsf + m_shiftb;
			}
			m_eld += m_shiftb;
			m_stretched_mcd = m_eld;
	
			if(m_manual_corr_status = YES)
			{
				m_eld = (m_eld - m_b) * m_rate + m_b;
			} 
			//cout << "---> " << m_mcd << " eld : " << m_eld << endl;
		} else 
		{	
			m_eld = m_mcd;
			if(m_affine_status == YES)
			{		
				m_mcd += m_shiftb;	
			} else 
				m_mcd = m_mbsf + m_shiftb;
			m_eld += m_shiftb;
			m_stretched_mcd = m_eld;

			if(m_manual_corr_status = YES)
			{			
				m_eld = (m_eld - m_b) * m_rate + m_b;
			}
			//cout << "2, " << m_stretch << " , " << m_depth << " , " << m_mcd << " , " << m_stretched_mcd << endl;

		}
		
		m_range.maxdepth = m_eld;
		m_range.mindepth = m_eld;	
		
		//cout << "m_stretch=" << m_stretch << ", m_number=" << m_number << ", m_mbsf=" << m_mbsf  << ", m_mcd=" << m_mcd <<  ", m_eld=" << m_eld  << endl;
		//cout << "m_number=" << m_number << ", m_mbsf=" << m_mbsf  << ", m_mcd=" << m_mcd <<  ", m_offset=" << m_offset  << endl;

		updateRange();	
		//std::cout <<  m_mcd << " , " << m_eld << " " << m_stretched_mcd << std::endl;
		//std::cout << "value updated " << m_offset << std::endl;
	}
}

double Value::getRawMcd(void)
{		
	return m_mbsf + m_offset + m_shiftb;	
}

double Value::calcDepthWithELD(double depth)
{
	/*if(m_corr_status == NO) 
	{
		std::cout << "Value::calcDepthWithELD = " << depth << std::endl;
		depth -= m_shiftb;
		depth -= m_offset;
		return depth;
	}*/
	
	double mbsf;
	double rate = m_stretch / 100.0f;
	//std::cout << "depth= " << depth << "rate= "<< rate << " b=" << m_b << " m_rate=" << m_rate << " shiftb=" << m_shiftb << std::endl;

	if(m_corr_status == YES)
	{
		if(m_manual_corr_status = YES)
		{
			mbsf = (depth-m_b) / m_rate + m_b ;
		} else 
		{
			mbsf = depth;
		}
		
		mbsf -= m_shiftb;
		mbsf = mbsf / rate - m_offset;
	} else 
	{
		mbsf = (depth-m_b) / m_rate + m_b ;
		mbsf -= m_shiftb;
		mbsf -= m_offset;
	}
	return mbsf;
}


void Value::updateLight( void )
{
	if(m_updated == true)
	{
		m_updated = false;
		if(m_quality & BAD_SB_DEPTH) 
		{			
			return;
		}
		if (m_cull_tabled == true)
		{
			return;
		}
		
		m_mcd = m_mbsf + m_offset;	
		if(m_corr_status == YES)
		{
			double rate = m_stretch / 100.0f;
			m_eld =  m_mcd * rate;	
			if(m_affine_status == YES)
			{
				m_mcd += m_shiftb;
			} else 
			{
				m_mcd = m_mbsf + m_shiftb;
			}
			m_eld += m_shiftb;
			m_stretched_mcd = m_eld;
	
			if(m_manual_corr_status = YES)
			{
				m_eld = (m_eld - m_b) * m_rate + m_b;
			} 
			//cout << "---> " << m_mcd << " eld : " << m_eld << endl;
		} else 
		{	
			m_mcd += m_shiftb;	
			m_stretched_mcd = m_mcd;
			m_eld = (m_mcd - m_b) * m_rate + m_b;
		}
	}
}

void Value::resetELD(void)
{ 
	double rate = m_stretch / 100.0f;
	if(m_affine_status == YES)
	{
		m_mcd = m_mbsf + m_offset;	
		m_eld = m_mcd * rate;	
	} else 
	{
		m_mcd = m_mbsf;	
		m_eld = m_mbsf * rate;	
	}
	m_stretched_mcd = m_eld;
	m_rate = 1.0f;
	m_b = 0.0f;	
	m_shiftb = 0.0f;
	//m_manual_corr_status = NO;
}
			
void Value::getTuple( string& data, int type )
{
	if(m_quality & BAD_SB_DEPTH) 
	{			
		return;
	} else if(m_cull_tabled == true)
	{
		//cout << "culled " << m_eld << " " <<  m_section << " " << getTop() << endl;
		return;
	} else if(m_quality==GOOD)
	{
		//cout << "not culled " << m_eld << " " <<  m_section << " " << getTop() << endl;

		char info[25];
		if(type == SMOOTH)  
		{
			if(m_valuetype == INTERPOLATED_VALUE) return; 
			sprintf(info, "%.2f,%.2f,", m_eld, m_data[1]);    
		} else 	if(type == SPLICESMOOTH)  
		{
			sprintf(info, "%.2f,%.2f,", m_mcd_splicer, m_data[1]);    
		} else 	if(type == LOGSMOOTH)  
		{
			sprintf(info, "%.2f,%.2f,", m_eld, m_data[1]);
		} else if (type == SPLICEDATA)
		{
			//cout << m_mcd_splicer << endl;
			sprintf(info, "%.2f,%.2f,", m_mcd_splicer, m_data[0]);    		
		} else  
		{
			if(m_valuetype == INTERPOLATED_VALUE) return;
			sprintf(info, "%.2f,%.2f,", m_eld, m_data[0]);    
		}
		data += info; 
		//cout << "mcd : " << m_mcd << " eld : " << m_eld << endl;	
	}
}

void Value::setRange( data_range range )
{
	if(m_range.top > range.top)	 // min
	{
		m_range.top = range.top;
	}
	if(m_range.bottom < range.bottom)	// max
	{
		m_range.bottom = range.bottom;
	}

	if(m_range.mindepth > range.mindepth)
	{
		m_range.mindepth = range.mindepth;
	}
	if(m_range.maxdepth < range.maxdepth)
	{
		m_range.maxdepth = range.maxdepth;
	}

	if(m_range.min > range.min)
	{
		m_range.min = range.min;
	}
	if(m_range.max < range.max)
	{
		m_range.max = range.max;
	}
	//cout << "value min  : " << m_range.min << " depth " << m_mbsf  << " " << m_number  << " " << m_data[1] - BAD_CODE << endl;
		
	m_range.realminvar = m_range.min;
	m_range.realmaxvar = m_range.max;
	//m_range.ratio = range.ratio;
	m_range.ratio = m_mbsf / m_mcd;
	
	m_range.avedepstep = range.avedepstep;
	
}

int Value::applyAffine( double offset, char type )
{
	if(m_quality & BAD_SB_DEPTH) 
	{			
		return 0 ;
	}
	
	if(m_type == type)
	{
		m_offset = offset;
		double depth = m_mbsf + offset;	
		setMcd(depth);
		m_affine_status = YES;
		return 1;
	} 
	return 0;
}

void Value::setSource(Value* source)
{
	m_source = source;
}

Value* Value::getSource(void)
{
	return m_source;
}
	
void Value::setNumber( int index )
{
	m_number = index;
}
																				
int Value::getNumber( void )
{
	return m_number;
}

void Value::setValueType( int type )
{
	m_valuetype = type;
}

void Value::setType( char type )
{
	m_type = type;
}

char Value::getType( void )
{
	return m_type;
}

void Value::setSection( char* value )
{
	strcpy(m_section, value);
	m_sectionId = atoi(value);
}

char* Value::getSection( void )
{
	return &m_section[0];
}

int Value::getSectionID( void )
{
	return m_sectionId;
}

void Value::setStretch( double rate, double b )
{
	m_rate = rate;
	m_b = b;
	m_manual_corr_status = YES;
	//m_shiftb = 0.0f;
	
	//cout << m_mcd  << " ";
	//m_eld = (m_mcd - b) * m_rate + b;
	//cout << m_eld << endl;
	m_updated = true;
	update();	
}

void Value::setB( double b )
{
	//cout << "m_shiftb = " << m_shiftb << " b =" << b << " ";
	m_manual_corr_status = YES;
	//m_rate = 1.0f;
	m_shiftb += b;
	//cout << "  :--------------: " << m_shiftb << endl;
	//setMcd(m_mcd);
	
	//cout << m_mcd  << " ";
	//m_eld = (m_mcd - b) * m_rate + b;
	//cout << m_eld << endl;
	
	m_updated = true;
	update();	
}

double Value::getRate( void )
{
	return m_rate;
}

double Value::getB( void )
{
	return m_b;
}

double Value::getShiftB( void )
{
	return m_shiftb;
}

double Value::getStrectchedMcd( void )
{
	return m_stretched_mcd;
}

void Value::setDepth( double depth )
{
	m_depth = depth;
	m_mbsf = depth;	
	m_mcd = depth;
	m_eld = depth;
	m_mcd_splicer = depth;
	
	if(fabs(m_mbsf - BAD_CODE) <= 1)
	{
		m_quality=BAD_SB_DEPTH;
	} else 
	{
		m_quality=GOOD;
		m_range.maxdepth = m_mbsf;
		m_range.mindepth = m_mbsf;
	}
	m_updated = true;
}

double Value::getDepth( void )
{
	return m_depth;
}


void Value::setRunNo( int num )
{
	m_runNumber = num;
}

int	Value::getRunNo( void )
{
	return m_runNumber;
}

void Value::setOtherOdp( double value )
{
	m_otherodp = value;
	m_updated = true;
}

double Value::getOtherOdp( void )
{
	return m_otherodp;
}

void Value::setMbsf( double mbsf ) 
{
	m_mbsf = mbsf;

	if(fabs(m_mbsf- BAD_CODE) <= 1)
	{
		m_quality=BAD_SB_DEPTH;
	} else
	{
		m_range.maxdepth = m_mbsf;
		m_range.mindepth = m_mbsf;
	}
	m_updated = true;
}

double Value::getMbsf( void )
{
	return m_mbsf;
}

void Value::setELD( double eld )
{
	m_eld = eld;	
}

double Value::getELD( void )
{
	//cout << m_mcd_splicer << " " << m_eld << endl;
	return m_eld;
}

void Value::setMcd( double mcd )
{
	m_mcd = mcd;
	m_mcd_splicer = m_mcd;

	if(fabs(m_mcd - BAD_CODE) <= 1)
	{
		m_quality=BAD_SB_DEPTH;
	} else
	{
		m_range.maxdepth = m_mcd;
		m_range.mindepth = m_mcd;
		
		double rate = m_stretch /100.0f;
		m_eld = m_mcd * rate;
		//cout << "---> " << m_mcd << " eld : " << m_eld << endl;
	}
	 
	m_updated = true;	
}

double Value::getMcd( void )
{
	return m_mcd;
}

double Value::getSpliceMcd( void )
{
	return m_mcd_splicer;
}

void Value::setSpliceMcd(  double mcd )
{
	m_mcd_splicer = mcd;
}

void Value::setRawData( double value )
{ 
	m_data[0] = value;
	m_data[1] = value;
	if(fabs(m_data[0] - BAD_CODE) <= 1)
	{
		m_quality=BAD_SB_DEPTH;
	} 
	
	m_updated = true;
	if(m_quality & BAD_SB_DEPTH) 
	{			
		return;
	}
	
	if(m_data[0]  > m_range.max) 
	{
		m_range.max = m_data[0];
	} 
	if(m_data[0] < m_range.min)
	{
		m_range.min = m_data[0];
	}	
	//cout << "min = " << m_range.min << " max = " << m_range.max << endl;
}

double Value::getRawData( void )
{
	return m_data[0];
}

void Value::setData( double value )
{ 
	m_data[1] = value;
	if(fabs(m_data[1] - BAD_CODE) <= 1)
	{
		m_quality=BAD_SB_DEPTH;
	} 
			

	m_updated = true;
	if(m_quality & BAD_SB_DEPTH) 
	{			
		return;
	}

	// I changed by HYEJUNG
	if(m_data[0]  > m_range.max) 
	{
		m_range.max = m_data[0];
	} 
	if(m_data[0] < m_range.min)
	{
		m_range.min = m_data[0];
	}
}

double Value::getData( void )
{
	if(m_quality & BAD_SB_DEPTH) 
	{			
		return BAD_PT;
	}
	return m_data[1];
}

int	Value::getValueType( void )
{
	return m_valuetype;
}

int Value::getCoreNumber( void )
{
	if(m_parent != NULL) 
	{
		Core* coreptr = (Core*) m_parent;
		return coreptr->getNumber();
	}	
	return -1;
}

void Value::setQuality( int quality )
{
	if(quality == BAD_CULLTABLE)
	{
		m_cull_tabled = true;
		CoreObject::setRange();
		m_updated = true;
		return;
	}
	
	if(m_parent != NULL) {
		Core* coreptr = (Core*) m_parent;
		if(quality != GOOD) 
		{
			coreptr->unrefGood();
		} else 
		{
			coreptr->refGood();
		}
	}
	m_quality = quality;

	if(m_quality != GOOD)
	{
		CoreObject::setRange();
	} 

  	m_updated = true;
}

int Value::getQuality( void )
{
	return m_quality;
}

void Value::setSmoothStatus( int status )
{
	m_smoothStatus = status;
}

int	Value::getSmoothStatus( void )
{
	return m_smoothStatus;
}

void Value::setStretch( double stretch )
{
#ifdef DEBUG
	if(m_valuetype == INTERPOLATED_VALUE)
			std::cout << "set stretch : interpolated_value " << std::endl;
#endif			
	m_stretch = stretch;
	m_corr_status = YES;	
	m_updated = true;
}

double Value::getStretch( void )
{
	return m_stretch;
}

double Value::getOffset( void )
{
	return m_offset;
}

int	Value::getDataFormat( void )
{
	if(m_parent) 
	{
		return m_parent->getDataFormat();
	}
	return -1;
}

int Value::check(char* leg, char* site , char* holename , int corenumber,  char* section)
{
	//if(section == NULL) return 0;
	
	// TEMPORARILY
	//if(strcmp(m_section, section) == 0)
	//{
		if (m_parent)
			return m_parent->check(leg, site, holename, corenumber);
	//}
	return 0;
}

	
#ifdef DEBUG
void Value::debugPrintOut( void )
{
	cout << " index : " << m_number << "  section : " << m_section << "  type : " << m_type << "  run number : " << m_runNumber <<  "  smooth status : ";
	switch(m_smoothStatus)
	{
	case UNSMOOTH:
		cout << "UNSMOOTH" << endl;
		break;
	case SMOOTH:
		cout << "SMOOTH" << endl;
		break;
	case SMOOTH_BOTH:
		cout << "SMOOTH_BOTH" << endl;
		break;
	case SM_OK:
		cout << "SM_OK" << endl;
		break;
	case SM_TAIL:
		cout << "SM_TAIL" << endl;
		break;					
	case TOOFEW_SMOOTHED:
		cout << "TOOFEW_SMOOTHED" << endl;
		break;	
	case SM_BAD_DATA:
		cout << "SM_BAD_DATA" << endl;
		break;		
	case SM_TOOFEWPTS:
		cout << "SM_TOOFEWPTS" << endl;
		break;
	case SM_BAD_CALC:
		cout << "SM_BAD_CALC" << endl;
		break;	
	}
	
	cout << " depth : " << m_depth << "  mbsf : " << m_mbsf << "  mcd : " << m_mcd <<"  eld : " << m_eld <<  "  otherodp : " << m_otherodp << "  mbsf/mcd : " << m_range.ratio << endl;
	cout << " data0 : " << m_data[0] << "  data1 : " << m_data[1] << "  top : " << m_range.top <<  " bottom : " << m_range.bottom << " min : " << m_range.min << " max : " << m_range.max;
	if(m_quality == GOOD) 
	{
		cout << "  quality : good" << endl;
	} else 
	{
		cout << "  quality : bad" << endl;
	}	
}
#endif
