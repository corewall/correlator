//////////////////////////////////////////////////////////////////////////////////
// CorrelatorLib - Correlator Class Library.  
//
// Module   :  Tie.cpp
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

#include <Tie.h>
#include <Core.h>
#include <Value.h>
#include <Actor.h>

#ifdef DEBUG
#include <iostream>
#endif

using namespace std;

TieInfo::TieInfo( void ) :  
m_coreptr(NULL), m_valueptr(NULL), 
m_mbsf(0.0f), m_mcd(0.0f), m_depth(0.0f), m_eld(0.0f), m_stretch(100.0f), m_top(0.0f), m_bottom(0.0f)
{ 
	memset(m_section, 0, 2); 
	m_valuetype ='\0'; 
}

Tie::Tie( Core* tiedcore, char valuetype, char* section, data_range range, double mbsf, double mcd, int type, bool fromFile ) :
  m_tietype(type), m_sharedFlag(false), m_nx(0), m_ref_count(0),
  m_coef(1.0f), m_offset(0.0f), m_cumOffset(0.0f), m_dummy(false),
  m_lead_lag(0), m_leadlag_in_meter(0.0f), m_constrained(true), m_isAll(false), m_active(true),
  m_b(0.0f), m_rate(1.0), m_applied(NO), m_order(0), m_fromFile(fromFile), m_isAppend(false),
  m_affine_status(NO), m_corr_status(NO), m_status(TIE_OK), m_straightFlag(false), m_isFirstShift(false)
{
	m_tiedcore.m_coreptr = tiedcore;
	m_tiedcore.m_valuetype = valuetype;
	strcpy(m_tiedcore.m_section, section);
	m_tiedcore.m_top = range.top;
	m_tiedcore.m_bottom = range.bottom;
	
	m_tiedcore.m_mbsf = mbsf;
	m_tiedcore.m_mcd = mcd;
	
	m_tiedcore.m_valueptr = findValue(0);
	//if(m_tiedcore.m_valueptr != NULL)
	//	cout << ">>>>>>>>>>> m_tiedcore tied " << m_tiedcore.m_valueptr->getELD();
}

Tie::Tie( int type /* = REAL_TIE */, bool fromFile /* = false */) :
  m_tietype(type), m_sharedFlag(false), m_nx(0), m_ref_count(0),
  m_coef(1.0f), m_offset(0.0f), m_cumOffset(0.0f), m_dummy(false),
  m_lead_lag(0), m_leadlag_in_meter(0.0f), m_constrained(true),  m_isAll(false), m_active(true),
  m_b(0.0f), m_rate(1.0), m_applied(NO), m_order(0), m_fromFile(fromFile),  m_isAppend(false),
  m_affine_status(NO), m_corr_status(NO), m_status(TIE_OK), m_straightFlag(false), m_isFirstShift(false)
{
	m_tiedcore.m_coreptr = NULL;
	m_tieTocore.m_coreptr = NULL;
}

Tie::~Tie( void )
{
}

void Tie::accept( Actor* flt )
{
	if(flt->getDataType() == TIE) 
	{
		flt->visitor(this);
	}
} 

void Tie::update( void )
{
	Value* valueA = NULL;
	Value* valueB = NULL;

	if(m_tietype == REAL_TIE)
	{
		if((m_isAppend == true) && (m_isAll == false))
		{
			m_updated =false;
		}
		if(m_constrained == false) 
		{	
			calcOffset();
		}
		
		valueA = findValue(0);
		//std::cout << "A : " << m_tiedcore.m_mcd << " " << m_tiedcore.m_mbsf << "  : "  << m_tieTocore.m_mcd << " " << m_tieTocore.m_mbsf << std::endl;
		if(valueA != NULL) 
		{
			//if(valueA->getELD() > m_tiedcore.m_mcd)
			//	m_tiedcore.m_valueptr = m_tiedcore.m_coreptr->getValue(valueA->getNumber() -1);
			//else 
			m_tiedcore.m_valueptr = valueA;
		} else 
		{
#ifdef DEBUG		
			std::cout << "[DEBUG] Tie : " << getId() << " could not find tie values A : " << m_tiedcore.m_mbsf << " " << m_tiedcore.m_coreptr->getName() << m_tiedcore.m_coreptr->getNumber() << std::endl;
#endif
			return;
		}		
		
		valueB = findValue(1);   // coreto
		if(valueB != NULL)
		{
			m_tieTocore.m_valueptr = valueB;
		} else 
		{
#ifdef DEBUG		
			std::cout << "[DEBUG] Tie : " << getId() << " could not find tie values B : " << m_tieTocore.m_mbsf  << " " << m_tieTocore.m_coreptr->getName() << m_tieTocore.m_coreptr->getNumber()  << std::endl;
#endif
			return;	
		}
	} else 
	{
		if(m_updated == true)
		{
			//std::cout << m_tiedcore.m_mcd << " " << m_tieTocore.m_mcd << std::endl;
			//std::cout << "inside ???Tie::update" << std::endl; 
			if(m_tiedcore.m_coreptr!= NULL &&  m_tiedcore.m_valueptr == NULL)
			{
				valueA = findValue(0);
				if(valueA != NULL) 
				{
					m_tiedcore.m_valueptr = valueA;
				} else 
				{
#ifdef DEBUG				
					std::cout << "[DEBUG] Tie : " << getId() << " could not find tie values A : " << m_tiedcore.m_mbsf << " " << m_tiedcore.m_coreptr->getName() << m_tiedcore.m_coreptr->getNumber() << std::endl;
#endif
					return;
				}		
			}
			
			if(m_tieTocore.m_coreptr!= NULL && m_tieTocore.m_valueptr == NULL)
			{
				valueB = findValue(1);   // coreto
				if(valueB != NULL)
				{
					m_tieTocore.m_valueptr = valueB;
				} else 
				{
					if(m_tietype != SAGAN_TIE)
					{
#ifdef DEBUG					
						std::cout << "[DEBUG] Tie : " << getId() << " could not find tie values B : " << m_tieTocore.m_mbsf  << " " << m_tieTocore.m_coreptr->getName() << m_tieTocore.m_coreptr->getNumber()  << std::endl;
#endif
						return;	
					}
				}
			}
			//if((valueB == NULL) || (valueB == NULL)) return;

			if(m_tietype == COMPOSITED_TIE)
			{
				// check offset and report to parent
				// setDepthOffset fromfile---> false
				if(m_applied == YES) 
				{
					calcOffset();
					m_tieTocore.m_coreptr->setDepthOffset(m_offset, m_tieTocore.m_valuetype, true);
				} else 
				{
					//m_tieTocore.m_coreptr->setDepthOffset(0, m_tieTocore.m_valuetype, true);

					double undo_offset = -m_tiedcore.m_mcd + m_tiedcore.m_valueptr->getELD();

					m_tieTocore.m_coreptr->setDepthOffset(undo_offset, m_tieTocore.m_valuetype, true);
				}
			}
			
			//if(calcCoefficient() <= 0) return;
			//std::cout << "coef : " << m_coef << std::endl;
		}
	}
	
	m_updated = false;
}


double Tie::getOffset(void)
{
	return m_offset;
}

void Tie::setConstrained(bool mode)
{
	m_constrained = mode;
}

bool Tie::isConstrained(void)
{
	return m_constrained;
}

bool Tie::isFromFile( void )
{
	return m_fromFile;
}

void Tie::setOrder(int order)
{
	m_order = order;
}

int Tie::getOrder(void)
{
	return m_order;
}

void Tie::setStrightFlag(bool flag)
{
	m_straightFlag = flag;
}

bool Tie::getStrightFlag(void)
{
	return m_straightFlag;
}	

void Tie::setFirstShiftFlag(bool flag)
{
	m_isFirstShift = flag;
}

bool Tie::isFirstShift(void)
{
	return m_isFirstShift;
}

void  Tie::setAppend(bool flag, bool all )
{
	m_isAppend = flag;
	m_isAll = all;
}

bool  Tie::isAppend(void)
{
	return m_isAppend;
}

bool Tie::isAll(void)
{
	return m_isAll;
}
	
void Tie::getTuple( string& data, int type )
{
	char info[125];  info[0] = 0;
	Core* coreA = m_tieTocore.m_coreptr;
	Core* coreB = m_tiedcore.m_coreptr;	
	if(coreA == NULL || coreB == NULL) return;
	/*if (m_tiedcore.m_valueptr)
	{
		m_tiedcore.m_mcd = m_tiedcore.m_valueptr->getMcd();
		//cout <<  m_tiedcore.m_valueptr->getMbsf() << " m_tiedcore.m_mcd : " << m_tiedcore.m_mcd << " " <<  m_tiedcore.m_valueptr->getTop() << " " <<  m_tiedcore.m_eld << endl;
	}
	if (m_tieTocore.m_valueptr)
	{
		m_tieTocore.m_mcd = m_tieTocore.m_valueptr->getMcd();
		//cout << " m_tieTocore.m_mcd : " << m_tieTocore.m_mcd << " " <<  m_tieTocore.m_valueptr->getTop() << endl;
	}*/
	if(type == SAGAN_TIE)
	{
		Value* valueptr = m_tiedcore.m_valueptr;
		if(valueptr != NULL)
		{
			/*double mcd = valueptr->getMbsf() + valueptr->getOffset();
			double rate = valueptr->getStretch() / 100.0f;
			double eld =  mcd * rate;
			double a = valueptr->getRate();
			double b = valueptr->getB();
			double shift = valueptr->getShiftB();
			cout << "a = " << a << " b = " << b << " shift = " << shift << " " << getOrder() << endl;
			//if ((a != 1.0) && (b != 0.0))
			{
				eld += shift - b;
			}*/
		
			sprintf(info, "%f,%f,", valueptr->getSpliceMcd(), valueptr->getELD());	
			//std::cout << info << std::endl;
		} else {
			printf( "error.......for tie.... NULL\n");
		}
	} else if (type == TIE_SHIFT)
	{
		if (m_active == true)
		{
			Value* valueptr = m_tieTocore.m_valueptr;
			if(valueptr != NULL)
			{
				sprintf(info, "%s,%d,%f,%f,", coreA->getName(), coreA->getNumber(), valueptr->getELD(), valueptr->getData());
			}
		}
	} else 
	{	
		if((m_isAll == false) && (m_isAppend == true))
		{
			//cout << "getTuple :: false true" << coreA->getName() << coreA->getNumber()<< endl;
			char* annotA = (char*) coreA->getParent()->getAnnotation();
			//cout << annotA  << endl;
			if(annotA == NULL)
				sprintf(info, "%d,%d,-,%s,%d,%f,%d,-,%s,%d,%f,:", -1, coreA->getType(), coreA->getName(), coreA->getNumber(), 0.0f, coreA->getType(), coreA->getName(), coreA->getNumber(), 0.0f);			
			else 
				sprintf(info, "%d,%d,%s,%s,%d,%f,%d,%s,%s,%d,%f,:", -1, coreA->getType(), annotA, coreA->getName(), coreA->getNumber(), 0.0f, coreA->getType(), annotA, coreA->getName(), coreA->getNumber(), 0.0f);			
			
			//cout << "append : " << info << endl;
		} else 
		{
			char* annotA = (char*) coreA->getParent()->getAnnotation();
			char* annotB = (char*) coreB->getParent()->getAnnotation();
			//cout << annotA <<  " " << annotB << endl;
			if(annotA == NULL)
			{ 
				if (annotB == NULL) 
					sprintf(info, "%d,%d,-,%s,%d,%f,%d,-,%s,%d,%f,:", getId(), coreA->getType(), coreA->getName(), coreA->getNumber(), m_tieTocore.m_mcd, coreB->getType(), coreB->getName(), coreB->getNumber(), m_tiedcore.m_mcd);
				else 
					sprintf(info, "%d,%d,-,%s,%d,%f,%d,%s,%s,%d,%f,:", getId(), coreA->getType(), coreA->getName(), coreA->getNumber(), m_tieTocore.m_mcd, coreB->getType(), annotB, coreB->getName(), coreB->getNumber(), m_tiedcore.m_mcd);
			} else 
			{
				if (annotB == NULL) 
					sprintf(info, "%d,%d,%s,%s,%d,%f,%d,-,%s,%d,%f,:", getId(), coreA->getType(), annotA, coreA->getName(), coreA->getNumber(), m_tieTocore.m_mcd, coreB->getType(), coreB->getName(), coreB->getNumber(), m_tiedcore.m_mcd);
				else 
					sprintf(info, "%d,%d,%s,%s,%d,%f,%d,%s,%s,%d,%f,:", getId(), coreA->getType(), annotA, coreA->getName(), coreA->getNumber(), m_tieTocore.m_mcd, coreB->getType(), annotB, coreB->getName(), coreB->getNumber(), m_tiedcore.m_mcd);
			}

			//cout << info << " " << m_tiedcore.m_valueptr->getMcd() << " " << m_tiedcore.m_valueptr->getELD() <<  endl;
		}
	}
	data += info;
}

int Tie::applyAffine( double offset, char type, int iscoreto /* = 1 */ )
{	
	//cout << "1 affine ";
	if(iscoreto == 1)
	{
		//cout << "1 affine ";
		if(m_tieTocore.m_valuetype != type) return 0;

		
		//int depth = m_tieTocore.m_mbsf + offset;
		//m_tieTocore.m_mcd = m_tieTocore.m_mbsf;

		//double rate = m_tieTocore.m_squish /100.0f;
		//m_tieTocore.m_eld = m_tieTocore.m_mcd * rate;	
	} else 
	{
		//cout << "2 affine ";
		
		if(m_tiedcore.m_valuetype != type) return 0;
		if(m_tietype != SAGAN_TIE)
		{
			//int depth = m_tiedcore.m_mbsf + offset;
			m_tiedcore.m_mcd = m_tiedcore.m_mbsf + offset;
			//std::cout << " 2 apply affine: " << offset << std::endl;

			double rate = m_tiedcore.m_stretch /100.0f;
			m_tiedcore.m_eld = m_tiedcore.m_mcd * rate;	
		}
	}
	
	//m_offset = offset;
	//m_updated = true;	

	m_affine_status = YES;	
	return 1;
}

int Tie::applyAffine( double offset )
{	
	if(m_tietype != SAGAN_TIE)
	{
		int depth = m_tieTocore.m_mbsf + offset;
		//m_offset = offset;
		m_tieTocore.m_mcd = depth;
		double rate = m_tieTocore.m_stretch /100.0f;
		m_tieTocore.m_eld = m_tieTocore.m_mcd * rate;	

		//cout << "******************" << endl;
	}
	//m_updated = true;	
	m_affine_status = YES;	
	return 1;
}

TieInfo* Tie::getInfoTieTo( void )
{
	return &m_tieTocore;
}

TieInfo* Tie::getInfoTied( void )
{
	return &m_tiedcore;
}

void Tie::calcEquation( Tie* tieptr )
{
	double tempdepth[2];
	if(m_corr_status == YES)
	{
		tempdepth[0] = m_tieTocore.m_eld;
	} else if (m_affine_status == YES)
	{
		tempdepth[0] = m_tieTocore.m_mcd;
	} else 
	{
		tempdepth[0] = m_tieTocore.m_mbsf;
	}
	if(tieptr != NULL) 
	{
		if(m_corr_status == YES)
		{
			tempdepth[1] = tieptr->m_tieTocore.m_eld;
		} else if (m_affine_status == YES)
		{
			tempdepth[1] = tieptr->m_tieTocore.m_mcd;	
		} else 
		{
			tempdepth[1] = tieptr->m_tieTocore.m_mbsf;	
		}
		// HJ
		//m_rate = (tieptr->m_tieTocore.m_depth - m_tieTocore.m_depth) / (tempdepth[1] - tempdepth[0]);
		//m_b = m_tieTocore.m_depth - (tempdepth[0] * m_rate); 	

		//cout << " rate : " << m_rate << " , " << m_b << endl;

	} else 
	{
		// HJ
		//m_rate = 1.0;
		//m_b = m_tieTocore.m_depth - tempdepth[0];	
	}
}

int Tie::calcCoefficient( int off )
{
	//  sum up
	//std::cout << "calcCoefficient " << std::endl;
	Core* coreA = m_tiedcore.m_coreptr;
	Core* coreB = m_tieTocore.m_coreptr;
 	int n = coreA->getNumOfValues() -1;
	int nY = coreB->getNumOfValues() -1;

	// find start value (in common region)
	double depthA = coreA->getValue(0)->getELD();
	double depthB = coreB->getValue(0)->getELD();
	double current_depth = depthA;
	Core* currentCore = coreB;
	if(current_depth < depthB)
	{
		current_depth = depthB;
		currentCore = coreA;
	}
	int start = findValueNumber(currentCore, current_depth);

	// find end value (in common region
	depthA = coreA->getValue(n)->getELD();
	depthB = coreB->getValue(nY)->getELD();
	currentCore = coreB;
	current_depth = depthA;
	if(current_depth > depthB)
	{
		current_depth = depthB;
		currentCore = coreA;
	}
	int end = findValueNumber(currentCore, current_depth);
	if((start <= 0) && (end <= 0)) return 0;
	if(start > end) return 0;

	double sumX = 0.0;
	double sumXsq = 0.0;
	double sumY = 0.0;
	double sumYsq = 0.0;
	double sumXYsq = 0.0;

	int nx = 0;
	double valueX, valueY;
	for(int i = start; i <= end; i++) 
	{
		valueX = coreA->getValue(i)->getData();	// could be okay... right??
		valueY = coreB->getValue(i)->getData();
	
		if(coreA->getValue(i)->getQuality() != BAD_PT || coreB->getValue(i)->getQuality() != BAD_PT) 
		{
			sumX = sumX + valueX;
			sumXsq = sumXsq + (valueX * valueX);
			sumY = sumY + valueY;
			sumYsq = sumYsq + (valueY * valueY);	
			sumXYsq =  sumXYsq + (valueX * valueY);	
			nx++;
		}
	} 

	// calculate the standard deviation and the correlation coefficient
	double stdevX, stdevY;
	if(nx > 1)
	{
		stdevX = (nx * sumXsq) - (sumX * sumX);
		stdevY = (nx * sumYsq) - (sumY * sumY);
		
		if(stdevX <= 0 || stdevY <= 0)
		{
			m_coef=0.0;
			return 0;
		} else 
		{

			stdevX = sqrt(stdevX);
			stdevY = sqrt(stdevY);	
			m_coef = ((nx * sumXYsq) - (sumX * sumY)) / (stdevX * stdevY);
		}
	} else 
	{
		m_coef=0.0;
	}
	m_nx = nx;
	
#ifdef DEBUG	
	std::cout << "[DEBUG] coef : " << m_coef << std::endl;
#endif	
	return 1;
}

int Tie::findValueNumber( Core* coreptr, double top )
{
	// find value
	int size = coreptr->getNumOfValues()-1;
	double valueX, valueY;
	Value* valueptr;
	int ret =0;
	int i;

	double topgabX, topgabY;
	for(i=0 ; i < size; i++)
	{
			valueX = coreptr->getValue(i)->getELD();
			valueY = coreptr->getValue(i+1)->getELD();
			
			topgabX =  top -  valueX;
			topgabY = top - valueY;
			if((topgabX >= -0.01) && (topgabY <= 0.01))
			{
				
					ret = 1;
					break;
			}
	}
	//std::cout << "Tie::top - " << top << ", value( " << valueX << ", " << valueY << " - " << ret  << " " <<  coreptr->getName() <<  coreptr->getNumber() << std::endl; 
	if(ret == 1)
			return i;
	return -1;

}

Value* Tie::findValue( Core* coreptr, double depth )
{
	// find value
	int size = coreptr->getNumOfValues() -1;
	double valueX, valueY;
	/*double gabX, gabY;
	for(int i=0 ; i < size; i++)
	{
			valueX = coreptr->getValue(i)->getELD();
			valueY = coreptr->getValue(i+1)->getELD();
			
			gabX =  depth -  valueX;
			gabY = depth - valueY;
			if((gabX >= -0.01) && (gabY <= 0.01))
			{
					valueptr = coreptr->getValue(i);
					break;
			}
	}
	//std::cout << "Tie::top - " << top << ", value( " << valueX << ", " << valueY << " - " << ret  << " " <<  coreptr->getName() <<  coreptr->getNumber() << std::endl; 
	*/
	
	double topgabX, topgabY;
	Value* valueptr = NULL;
	Value* valueptrA = NULL;
	Value* valueptrB = NULL;
	for(int i=0 ; i <= size; i++) 
	{
		valueptrA = coreptr->getValue(i);
		valueptrB = coreptr->getValue(i+1);
		if(valueptrA == NULL || valueptrB == NULL) continue;
		valueX = valueptrA->getMcd();
		valueY = valueptrB->getMcd();
		//std::cout << valueX << " " << depth  << " " <<  valueY << std::endl;
		
		if(valueX == depth) 
		{
			//std::cout << "A " <<  valueX << " " << valueY << " : " << depth << " " <<   std::endl;
			return valueptrA;
		}
		if(valueY == depth)	
		{
			//std::cout << "B "  << valueX << " " << valueY << " : " << depth << " " <<   std::endl;
			return valueptrB;
		}

		topgabX =  depth -  valueX;
		topgabY = depth - valueY;
		//std::cout << depth  << " - " <<  valueY << " = " << topgabY << std::endl;
		if(topgabY == 0.0)
		{
			//std::cout << "B- "  << valueX << " " << valueY << " : " << depth << " " <<   std::endl;
			valueptr = valueptrB;
			break;
		}
		
		if((topgabX >= -0.01) && (topgabY < 0.00)) 	//if((top >= valueX) && (top <= valueY))
		{
			valueptr = valueptrA;
			break;
		}
	} 	 
	//std::cout << valueX << " " << valueY << " : " << depth << " " <<   std::endl;	
		
	return valueptr;
}




int Tie::calcCoefficientUpdate( int off )
{
	//  sum up
	Core* coreA = m_tiedcore.m_coreptr;
	Core* coreB = m_tieTocore.m_coreptr;
 	int n = coreA->getNumOfValues();
	int nY = coreB->getNumOfValues();
	if(nY < n)
	{
		n = nY;
	}
	
	int size = off + n;
	if(n < 1 || size > n) 
	{
		return 1;
	} 
	double sumX = 0.0;
	double sumXsq = 0.0;
	double sumY = 0.0;
	double sumYsq = 0.0;
	double sumXYsq = 0.0;

	double rate = m_tieTocore.m_stretch /100.0f;

	int nx = 0;
	double valueX, valueY;
	for(int i = off; i < size; i++) 
	{
		valueX = coreA->getValue(i)->getMbsf();	// could be okay... right??
		valueY = coreB->getValue(i)->getMbsf() + m_offset;
		valueY = valueY * rate;

		if(valueX != BAD_PT || valueY != BAD_PT) 
		{
			sumX = sumX + valueX;
			sumXsq = sumXsq + (valueX * valueX);
			sumY = sumY + valueY;
			sumYsq = sumYsq + (valueY * valueY);	
			sumXYsq =  sumXYsq + (valueX * valueY);	
			nx++;
		}
	} 
	
	// calculate the standard deviation and the correlation coefficient
	double stdevX, stdevY;
	if(nx > 1)
	{
		stdevX = (nx * sumXsq) - (sumX * sumX);
		stdevY = (nx * sumYsq) - (sumY * sumY);
		
		if(stdevX <= 0 || stdevY <= 0)
		{
			m_coef=0.0;
			return 0;
		} else 
		{
			stdevX = sqrt(stdevX);
			stdevY = sqrt(stdevY);	
			m_coef = ((nx * sumXYsq) - (sumX * sumY)) / (stdevX * stdevY);
//cout << "1 : " << stdevX << " " << stdevY << " sumX " << sumX << " sumY " << sumY << " sumXYsq " << sumXYsq << " coef " << m_coef  << " offset " << m_offset << " rate "  << rate << endl;	
		}
	} else 
	{
		m_coef=0.0;
	}
	m_nx = nx;
	
	return 1;
}


int Tie::calcOffset( void )
{
	//m_offset = m_tiedcore.m_mcd - m_tiedcore.m_mbsf;
	//m_offset += m_tiedcore.m_mbsf - m_tieTocore.m_mbsf;
	
	//m_offset = m_tieTocore.m_valueptr->getMcd() - m_tieTocore.m_valueptr->getMbsf();
	m_offset = m_tieTocore.m_coreptr->getDepthOffset();
	//cout << "1. core offset = " << m_offset << endl;
	m_offset +=  m_tiedcore.m_mcd - m_tieTocore.m_mcd;
	//cout << "offset = " << m_tiedcore.m_mcd - m_tieTocore.m_mcd  << " offset =" << m_offset << endl;
	//cout << "in calcoffset : " << m_offset  << " " << m_tiedcore.m_mbsf << " " <<  m_tieTocore.m_mbsf <<  endl;
	return 1;
}

int Tie::correlate( void )
{
	// TieCorrelate
	// calc. the depth offset at tie
	//double  tiedepoffset = m_tiedcore->getValue(i)->getMcd() - m_tieTocore->getValue(i)->getMcd();

	// get the window length and find the first value(array member) of core 2
	// that is within the window. then count out to the last value that is in the window
	
	//double depstep;
	
	// the lead,lag(in meters) and find the lead,lag in data points
	// m_leadlag_in_meter : from user 
/*	int num_lead_lag, lag;
	if(m_leadlag_in_meter > 0.0)
	{
		m_lead_lag = m_leadlag_in_meter/depstep;
		num_lead_lag = m_lead_lag * 2 + 1;
		lag = -1.0 * m_lead_lag;
	} else 
	{
		m_lead_lag=0;
		lag=0;
	}
  */
	// calc. corr. coef. for each lead,lag in given window note that core1offset causes core 1 to lag and then lead core 2
	//core1offset = tie1num - tie2num - lag;
	//calcCoefficient();

//	m_lead_lag = lag;
	//m_offset = m_tiedcore->getValue(i)->getELD() - m_tieTocore->getValue(i)->getELD() - lag * depstep;
	//corr.depleadlag[dset][corr.num_lead_lag[dset]] = lag * depstep;
 
	// find the highest corr. coef. and save its array member number and draw the correlation
  
	// correlate any other data sets
 
	return 1;
}

void Tie::setTieTo( Core* coreptr, char valuetype, char* section, data_range range, double mbsf /* =0.0 */, double mcd /* =0.0 */ )
{
	m_tieTocore.m_coreptr = coreptr;
	m_tieTocore.m_valuetype = valuetype;
	if(section != NULL)
	{
		strcpy(m_tieTocore.m_section, section);
	}
	m_tieTocore.m_top = range.top;
	m_tieTocore.m_bottom = range.bottom;
	m_tieTocore.m_mbsf = mbsf;
	m_tieTocore.m_mcd = mcd;
	//m_updated = true;
	m_tieTocore.m_valueptr = findValue(1);

	//if(m_tieTocore.m_valueptr != NULL)
	//	cout << ">>>>>>>>>>> m_tieTocore tied " << m_tieTocore.m_valueptr->getELD();	
	//m_tieTocore.m_valueptr = valueptr;
}

void Tie::setTied( Core* coreptr, char valuetype, char* section, data_range range, double mbsf /* = 0.0*/, double mcd /* = 0.0 */ )
{
	m_tiedcore.m_coreptr = coreptr;
	m_tiedcore.m_valuetype = valuetype;
	if(section != NULL)
	{
		strcpy(m_tiedcore.m_section, section);
	}
	m_tiedcore.m_top = range.top;
	m_tiedcore.m_bottom = range.bottom;
	m_tiedcore.m_mbsf = mbsf;
	m_tiedcore.m_mcd = mcd;
	m_tiedcore.m_valueptr =findValue(0);
	//if(m_tiedcore.m_valueptr != NULL)
	//	cout << ">>>>>>>>>>> m_tiedcore tied " << m_tiedcore.m_valueptr->getELD();
	m_updated = true;
}

void Tie::setTieTo( Value* valueptr)
{
	if(valueptr== NULL) return;
	m_tieTocore.m_valueptr = valueptr;
	m_updated = false;
}

void Tie::setTied( Value* valueptr)
{
	if(valueptr== NULL) return;
	m_tiedcore.m_valueptr = valueptr;
	m_updated = false;
}

void Tie::setTied( double mcd )
{
	m_tiedcore.m_mcd = mcd;
}

Core* Tie::getTieTo( void )
{
	return m_tieTocore.m_coreptr;
}

Core* Tie::getTied( void )
{
	return m_tiedcore.m_coreptr;
}

Value* Tie::getTiedValue( void )
{
	return m_tiedcore.m_valueptr;
}

Value* Tie::getTieToValue( void )
{
	return m_tieTocore.m_valueptr;
}
	
double Tie::getCoef( void ) 
{
	calcCoefficient();
	return m_coef;
}

void Tie::setType( int type )
{
	m_tietype = type;
}

int Tie::getType( void )
{
	return m_tietype;
}

void Tie::setSharedFlag( bool flag )
{
	m_sharedFlag = flag;
}

bool Tie::getSharedFlag( void )
{
	return m_sharedFlag;
}

	
// indicate that tie is to be applied (versus undone)
void Tie::setApply( int applied )
{
	m_applied = applied;
	m_updated = true;
}

void Tie::setStretch( double stretch, int iscoreto )
{
	/*if(iscoreto == 1)
	{
		m_tieTocore.m_stretch = stretch;
	} else 
	{
		m_tiedcore.m_stretch = stretch;
	}
	m_updated = true;*/
}	
	
void Tie::setRate( double rate )
{
	m_rate = rate;
}

double Tie::getRate( void )
{
	return m_rate;
}

void Tie::setB( double b )
{
	m_b = b;
}

double Tie::getB( void )
{
	return m_b;
}

void Tie::setRateandB( double rate, double b )
{
	m_rate = rate;
	m_b = b;
}


Value* Tie::createInterpolatedValue(Core* coreptr, double mcd, Value* valueptr)
{
	double depth = mcd - coreptr->getDepthOffset();
	

	int idx = valueptr->getNumber();
	Value* prev_Value =NULL;
	Value* next_Value =NULL;	
	if(mcd < valueptr->getMcd())
	{
		prev_Value = coreptr->getValue(idx-1);
		next_Value = valueptr;
	} else 
	{
		prev_Value = valueptr;
		next_Value = coreptr->getValue(idx+1);
	}
	// to varify...
#ifdef DEBUG	
	std::cout << "[DEBUG] prev=" <<  prev_Value->getMcd() <<  " mcd=" << mcd  << " next=" << next_Value->getMcd() << std::endl;
	if((mcd > prev_Value->getMcd()) && (mcd < next_Value->getMcd()))
		std::cout << "[DEBUG] ... in range " << std::endl;
#endif		
	
	Value* newValue = coreptr->createInterpolatedValue(depth);
	double temp_data, temp_top;
	if(newValue && (newValue->getMbsf() != depth))
	{

		double temp_data = valueptr->getRawData();
		double diff_depth = next_Value->getMcd() - prev_Value->getMcd();
		double diff_data = next_Value->getData() - prev_Value->getData();
		double a, b;
		if (diff_data == 0)
			temp_data = next_Value->getData();
		else if (diff_depth == 0)
			temp_data = next_Value->getData();
		else
		{ 	
			a = diff_depth / diff_data;
			b = next_Value->getMcd() - a * next_Value->getData();
			temp_data = (mcd - b) / a;
			//std::cout << prev_Value->getData() << " " << temp_data  << " " << next_Value->getData() << std::endl;
		}
									
		temp_top =prev_Value->getTop() + (mcd - prev_Value->getMcd()) * 100;
	
		newValue->copy(valueptr);
		newValue->setDepth(depth);
		newValue->applyAffine(coreptr->getDepthOffset(), newValue->getType());
		// need to update data and bottom/top value				
		newValue->setRawData(temp_data);		
		newValue->setTop(temp_top);		
		//std::cout << "[DEBUG] new value is created.... " << newValue->getTop() << " " <<  newValue->getMbsf() << ", " << newValue->getMcd() << std::endl;
	}
	return newValue;
}

Value* Tie::findValue( int iscoreto )
{
	Core* coreptr = NULL;
	if(m_isAppend == true) return NULL;
	
	if (m_dummy == true)
	{
		//std::cout << "dummy.......... " << m_tieTocore.m_mbsf << std::endl;
		coreptr = m_tieTocore.m_coreptr;
		int value_index = coreptr->getNumOfValues()-1;
		return coreptr->getValue(value_index);
	}
	
	Value* valueptr = NULL;
	char section[2];
	double top, bottom, mbsf;
	if(iscoreto == 1)
	{
		// brgtodo 5/27/2014: else block uses m_tiedCore instead of m_tieTocore, otherwise identical
		coreptr = m_tieTocore.m_coreptr;
		strcpy(section, m_tieTocore.m_section);
		top =  m_tieTocore.m_top;
		bottom = m_tieTocore.m_bottom;
		mbsf = m_tieTocore.m_mbsf;

		// need to find mbsf again.... 
		if(m_tietype == REAL_TIE)
		{
			if(m_tieTocore.m_valueptr != NULL)
			{
				if((m_tieTocore.m_valueptr->isCorrelated() == NO)  && (m_tieTocore.m_valueptr->isMannualCorrelated() == NO))
				{
					//m_tieTocore.m_mcd = m_tieTocore.m_valueptr->getMcd();
					
					valueptr = findValue(coreptr, m_tieTocore.m_mcd);
					if(valueptr != NULL)
					{
						if(m_tieTocore.m_mcd != valueptr->getMcd())
						{
							if(m_tieTocore.m_valueptr->getValueType() == INTERPOLATED_VALUE)
							{
								coreptr->deleteInterpolatedValue(m_tieTocore.m_valueptr->getNumber());
							}					
							valueptr = createInterpolatedValue(coreptr, m_tieTocore.m_mcd, valueptr);
						}
						//std::cout << " update find/ tie to " << m_tieTocore.m_mcd << " " << valueptr->getMcd() << std::endl;		
		
						//std::cout << "something changed .... 1 " << m_tieTocore.m_mcd << " " << valueptr->getMcd() << " " << m_tieTocore.m_valueptr->getMcd() << std::endl;
						//m_tieTocore.m_valuetype = valueptr->getValueType();
						//strcpy(m_tieTocore.m_section, section);
						m_tieTocore.m_top = valueptr->getTop();
						m_tieTocore.m_bottom = valueptr->getBottom();
						m_tieTocore.m_mbsf = valueptr->getMbsf();
						return valueptr;
					} else 
					{
#ifdef DEBUG					
						//std::cout << " could not find... -find/ tie to " << std::endl;
						std::cout << "[DEBUG] ERROR : could not find./ tie to " << coreptr->getName() << coreptr->getNumber() << " " << m_tieTocore.m_mcd << " " << m_tieTocore.m_valueptr->getMcd() << std::endl;		
						std::cout << "[DEBUG]  " << coreptr->getMinDepth() << " " << coreptr->getMaxDepth() << std::endl;
#endif
						return m_tieTocore.m_valueptr;
					}
				}
			}
		}
		//cout << "tie top " << top << " bottom " << bottom << " mbsf " << mbsf << endl;
	} else 
	{
		coreptr = m_tiedcore.m_coreptr;
		strcpy(section, m_tiedcore.m_section);
		top =  m_tiedcore.m_top;
		bottom = m_tiedcore.m_bottom;	
		mbsf = m_tiedcore.m_mbsf;

		if(m_tietype == REAL_TIE)
		{
			if(m_tiedcore.m_valueptr != NULL)
			{	
				//m_tiedcore.m_mcd = m_tiedcore.m_valueptr->getMcd();
				if((m_tiedcore.m_valueptr->isCorrelated() == NO)  && (m_tiedcore.m_valueptr->isMannualCorrelated() == NO))
				{
		
					valueptr = findValue(coreptr, m_tiedcore.m_mcd);
					if(valueptr != NULL)
					{					
						if(m_tiedcore.m_mcd != valueptr->getMcd())
						{
							if(m_tiedcore.m_valueptr->getValueType() == INTERPOLATED_VALUE)
							{
								coreptr->deleteInterpolatedValue(m_tiedcore.m_valueptr->getNumber());
							}
							valueptr = createInterpolatedValue(coreptr, m_tiedcore.m_mcd, valueptr);
						} 
						//std::cout << " update find/ tied " << m_tiedcore.m_mcd << " " << valueptr->getMcd() << std::endl;		

						//std::cout << "something changed .... 2 " << m_tiedcore.m_mcd << " " << valueptr->getMcd() << " " << m_tiedcore.m_valueptr->getMcd() << std::endl;
						//m_tiedcore.m_valuetype = valueptr->getValueType();
						//strcpy(m_tiedcore.m_section, section);
						m_tiedcore.m_top = valueptr->getTop();
						m_tiedcore.m_bottom = valueptr->getBottom();
						m_tiedcore.m_mbsf = valueptr->getMbsf();
						return valueptr;
					} else 
					{
#ifdef DEBUG					
						std::cout << "[DEBUG] ERROR : could not find./ tied " << coreptr->getName() << coreptr->getNumber() << " " << m_tiedcore.m_mcd << " " << m_tiedcore.m_valueptr->getMcd() << std::endl;		
#endif
						//std::cout << coreptr->getMinDepth() << " " << coreptr->getMaxDepth() << std::endl;
						//std::cout << " could not find... -find/ tied " << std::endl;
						return m_tiedcore.m_valueptr;
					}
				}
			}
		}
	
		//cout << "tie top " << top << " bottom " << bottom << " mbsf " << mbsf << endl;			
	}
	if (coreptr == NULL) return NULL;
		
	// find value
 	int size = coreptr->getNumOfValues();
	//cout << " findValue top : " << top << " " << coreptr->getName() << coreptr->getNumber() << " " << section << " " << size << endl;

	double valueX, valueY;
	int foundsection=0, i=0;

	// check it's is in range
	size--;
	double gabX, gabY;
	if(size > 0)
	{
		valueX = coreptr->getValue(0)->getMbsf();
		valueY = coreptr->getValue(size)->getMbsf();

		if (valueX > mbsf) 
		{	
			gabX = valueX-mbsf;
			if(gabX < 1) 
			{
				//cout << "[DEBUG/Tie] : User the first value" << endl;
				return coreptr->getValue(0);
			}
#ifdef DEBUG			
			cout << "[DEBUG/Tie] Error: " << mbsf << " is not in range (start=" << valueX << ")" << endl;
#endif
			return NULL;
		} else if (mbsf > valueY)
		{	
			gabY = mbsf - valueY;
			if(gabX < 1) 
			{
				//cout << "[DEBUG/Tie] : User the last value" << endl;
				return coreptr->getValue(size);
			}		
#ifdef DEBUG			
			cout << "[DEBUG/Tie] Error: " << mbsf << " is not in range (end=" << valueY << ")" << endl;
#endif
			return NULL;
		}
	}

	for(; i < size; i++) 
	{
		valueX = coreptr->getValue(i)->getMbsf();
		valueY = coreptr->getValue(i+1)->getMbsf();
		
		if(valueX == mbsf) 
		{
			valueptr = coreptr->getValue(i);
			break;
		}
		if(valueY == mbsf)	
		{
			valueptr = coreptr->getValue(i+1);
			break;
		}
		

		gabX = mbsf - valueX;
		gabY = mbsf - valueY;
		//std::cout << "mbsf=" << mbsf << " valueX=" << valueX << " valueY=" << valueY << " gabX=" << gabX << " gabY=" << gabY << endl;
		if(gabY == 0.0)
		{
			valueptr = coreptr->getValue(i+1);
			break;
		}
		
		if((gabX >= -0.01) && (gabY < 0.00)) 	
		{
			valueptr = coreptr->getValue(i);
			break;
		}
		//if(top == valueX) 
		if(mbsf == valueX) 
		{
			valueptr = coreptr->getValue(i);
			break;
		}
		if(mbsf == valueY) 
		{
			valueptr = coreptr->getValue(i+1);
			i++;
			break;
		}		
	} 	
	return valueptr;
	
}

#ifdef DEBUG
void Tie::debugPrintOut( void )
{
	cout << "[Tie] tired core number : " << m_tiedcore.m_coreptr->getNumber() <<  ", " << m_tieTocore.m_coreptr->getNumber();
	if(m_status == TIE_ERROR)
	{
		cout << "  error - could not find the core" << endl;
	} else 
	{
		cout << "  coef : " << m_coef << "  offset : " << m_offset;
		if(m_applied == YES) 
		{
			cout << "  applied : Y";
		} else 
		{
			cout << "  applied : N";
		}
		if(m_tietype == COMPOSITED_TIE)
		{
			cout << "  type: composite" << endl;
		} else if (m_tietype == REAL_TIE)
		{
			cout << "  type : splice" << endl;
		} else if (m_tietype == INTERPOLATED_TIED)
		{
			cout << " type : interporate" << endl;
		}
	}
		
	cout << "type : " << m_tiedcore.m_valuetype << "  section : " << m_tiedcore.m_section;
	if(m_tietype == COMPOSITED_TIE)
	{ 
		cout << "  mbsf : " << m_tiedcore.m_mbsf << "  mcd : " << m_tiedcore.m_mcd;
	} else 
	{
		cout << "  depth : " << m_tiedcore.m_mbsf;
	}
	cout << "  top : " << m_tiedcore.m_top << "  bottom : " << m_tiedcore.m_bottom << " tie to " << endl; 
	cout << "type : " << m_tieTocore.m_valuetype << "  section : " << m_tieTocore.m_section;
	if(m_tietype == COMPOSITED_TIE)
	{ 
		cout << "  mbsf : " << m_tieTocore.m_mbsf << "  mcd : " << m_tieTocore.m_mcd;
	} else 
	{
		cout << "  depth : " << m_tieTocore.m_mbsf;
	}
	cout << "  top : " << m_tieTocore.m_top << "  bottom : " << m_tieTocore.m_bottom << endl;
}
#endif
