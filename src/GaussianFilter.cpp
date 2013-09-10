//////////////////////////////////////////////////////////////////////////////////
// CorrelatorLib - Correlator Class Library.  
//
// Module   :  GaussianFilter.cpp
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
#include <stdio.h>

#include <CoreTypes.h>
#include <GaussianFilter.h>
#include <Value.h>
#include <Core.h>

#ifdef DEBUG
#include <iostream>
#endif

#ifdef WIN32
#define rint(a) floor((a)+(((a) < 0)? -0.5 : 0.5))
#endif

using namespace std;

GaussianFilter::GaussianFilter( int value, int unit )
: m_width(value), m_unit(unit), 
  m_weight(NULL), m_maxdepth(0), m_depth(0),
  m_datptr(NULL), m_sm_datptr(NULL),
  m_usedepth(0), m_plot(SMOOTH)
{
	m_datatype = CORE;
	
	if (unit == DEPTH)
	{
		m_depth = value;
		m_width = 0;
	}
	
#ifdef DEBUG
	/*
	cout << "[GaussianFilter] Smoothing : ";
	if(m_unit == POINTS) 
	{
		cout << m_width << "  Points  ";
	} else 
	{
		cout << m_depth << "  Depth (cm)  ";

	}	
	switch(m_plot)
	{
	case UNSMOOTH:
		cout << "Plot Display : Unsmoothed" << endl;
		break;
	case SMOOTH:
		cout << "Plot Display : Smoothed" << endl;	
		break;
	case SMOOTH_BOTH:	
		cout << "Plot Display : Both Smoothed" << endl;	
		break;
	}
	*/
#endif	

	setWidth(m_width);
}

GaussianFilter::~GaussianFilter( void )
{
	if(m_weight != NULL)
	{
		free(m_weight);
		m_weight = NULL;
	}
	
	if(m_datptr != NULL)
	{
		free(m_datptr);
		m_datptr = NULL;
	}
	
	if(m_sm_datptr != NULL)
	{
		free(m_sm_datptr);
		m_sm_datptr = NULL;
	}	
}

void GaussianFilter::init( void )
{
	m_width = 0;
	m_enable =false;
}

void GaussianFilter::visitor( CoreObject* object )
{
	if(m_enable == false) return;
	if(m_weight == NULL) return;
	
	// loop through cores
	switch(m_unit)
	{
	case POINTS :
		visitorPoints(object);
		break;
	case DEPTH :
		visitorDepth(object);
		break;
	}
	
}

void GaussianFilter::visitorPoints( CoreObject* object )
{
	if(m_datptr == NULL) return;
	
	Core* coreptr = (Core*) object;

	int halfwidth = (m_width -1) / 2;
	
	// loop through data (first and last "halfwidth" values are same as raw data if good!)
	int numvalues = coreptr->getNumOfValues();
	Value* valueptrI = NULL;
	Value* valueptrJ = NULL;

	int i=0;	
    for(i = 0; i < halfwidth && i < numvalues; i++)
	{
		valueptrI = coreptr->getValue(i);
		if(valueptrI->getQuality() == GOOD)
		{
			valueptrI->setSmoothStatus(SM_TAIL);
		} else 
		{
			valueptrI->setSmoothStatus(SM_BAD_DATA);
		}
	}
	
	if(i >= numvalues)
	{
		coreptr->setSmoothStatus(SM_TOOFEWPTS);	
	} else 
	{ 
		int lasthalfwidth = numvalues-halfwidth; 
		int inc;

		// loop through data until at last half width
		int datptr_cnt = 0; // ?????? 
		int num_interp = 0;
		int qualityI, qualityJ;
		double tempdata =0;
		
		for(; i < lasthalfwidth; i++)
		{
			valueptrI = coreptr->getValue(i);
			qualityI = valueptrI->getQuality();
			
			// let smooth be ok until proven otherwise
			valueptrI->setSmoothStatus(SM_OK);	
			// first value in smoothing 
			inc = i - halfwidth;    

			// raw value at this point must be good 
			if(qualityI != GOOD)
			{
				valueptrI->setSmoothStatus(SM_BAD_DATA);
			} else {
				// fill data arrays
				datptr_cnt = 0;
				num_interp = 0;
				Value* valueptrL = NULL;
				Value* valueptrM = NULL;	
				for(int j = inc; datptr_cnt < m_width && j < numvalues; j++, datptr_cnt++)
				{
					valueptrJ = coreptr->getValue(j);
					qualityJ = valueptrJ->getQuality();
					
					if(qualityJ == GOOD)
					{
						m_datptr[datptr_cnt] = valueptrJ->getData();
					} else 
					{	// interpolate data point
						// find next lower point in width range
						int l;
						for(l = j - 1; l >= inc && coreptr->getValue(l)->getQuality() != GOOD; l--);

						// no lower point in range 
						if(l < inc)       
						{
							valueptrI->setSmoothStatus(SM_TOOFEWPTS);
						} else
						{
							int m;
							// find next higher point in width range
							for(m = j + 1; m <= i + halfwidth && coreptr->getValue(m)->getQuality() != GOOD; m++);
						  
							// no higher point in range
							if(m > i + halfwidth )     
							{
								valueptrI->setSmoothStatus(SM_TOOFEWPTS);
							} else 
							{
								valueptrL = coreptr->getValue(l);
								valueptrM = coreptr->getValue(m);				
							
								if(m_usedepth == 0) 
								{				
									m_datptr[datptr_cnt] = valueptrL->getData() + (valueptrM->getData() - valueptrL->getData()) * 
													  (valueptrM->getMbsf() - valueptrL->getMbsf()) / valueptrJ->getMbsf();													    
								} else 
								{
									//m_datptr[datptr_cnt] = valueptrL->getData() + (valueptrM->getData() - valueptrL->getData()) * 
									//				  (valueptrM->getDepth() - valueptrL->getDepth()) / valueptrJ->getDepth();  
								}
								num_interp++;
							}
						}
					}
				} // end of for statement
			}

			if(num_interp > halfwidth)
			{
				  valueptrI->setSmoothStatus(SM_BAD_CALC);
			}
			
			// compute smoothed value
			if(valueptrI->getSmoothStatus() < SM_OK)
			{
			} else if (!valueptrI->getQuality())
			{
				tempdata =0;
				for(int j = 0; j < m_width; j++)
				{
					tempdata +=  m_datptr[j] * m_weight[j+1];
				}
				valueptrI->setData(tempdata);
			} else 
			{
				valueptrI->setSmoothStatus(SM_BAD_CALC);
			}
			
		} // end of for statement

		if(i < numvalues)
		{
			// loop through last half width values 
			for(; i < numvalues; i++)
			{
				if(valueptrI->getQuality() == GOOD)
				{
					valueptrI->setSmoothStatus(SM_TAIL);
				} else 
				{
					valueptrI->setSmoothStatus(SM_BAD_DATA);
				}
			}
		}

		// check if have some smoothed points
		int count = 0;
		for(i = 0; i < numvalues; i++)
		{
			valueptrI = coreptr->getValue(i);
			if(valueptrI->getSmoothStatus() == SM_OK || valueptrI->getSmoothStatus() == SM_TAIL)
			{
				++count;
			}
		}
		if(count < TOOFEW_SMOOTHED)
		{
			coreptr->setSmoothStatus(SM_TOOFEWPTS);
		}
		
		if(coreptr->getSmoothStatus() == NONE) 
		{
			coreptr->setSmoothStatus(SM_OK);
		}
	} // end of if-else statement

}
 
void GaussianFilter::visitorDepth( CoreObject* object ) 
{
	Core* coreptr = (Core*) object;
	if(coreptr == NULL) return;
	coreptr->setSmoothStatus(NONE);
		
	int halfwidth = (m_depth -1) / 2;
	
	// find first & last good points
	int numvalues = coreptr->getNumOfValues();
	Value* valueptrI = NULL;
	Value* valueptrJ = NULL;
	Value* valueptrM = NULL;
	
	int i, j;
	
	for(i = 0; i < numvalues && coreptr->getValue(i)->getQuality() != GOOD; i++);
 	for(j = numvalues-1; j >= 0 && coreptr->getValue(j)->getQuality() != GOOD; j--);

 
	int end_cnt = j;
	if(end_cnt < 0 || i >= numvalues)
	{
		coreptr->setSmoothStatus(SM_TOOFEWPTS);
	} else
	{
		valueptrI =  coreptr->getValue(i);
		if (valueptrI == NULL) return;
		valueptrJ =  coreptr->getValue(end_cnt);
		if (valueptrJ == NULL) return;
		
		double start_depth;
		double end_depth;
		if(m_usedepth == 0)
		{
			start_depth = valueptrI->getMbsf() * 100.0;
			end_depth = valueptrJ->getMbsf() * 100.0;
		} else 
		{
			start_depth = valueptrI->getDepth() * 100.0;
			end_depth = valueptrJ->getDepth() * 100.0;
		}
		//cout << " max = " << m_maxdepth << " start = " << start_depth << " end = " << end_depth << endl;
			
		int num_depths = 1 + (int) (end_depth - start_depth);

		if(num_depths <= halfwidth)
		{
			coreptr->setSmoothStatus(SM_TOOFEWPTS);
#ifdef DEBUG			
			cout << "num_depths <= halfwidth" << endl;
#endif
		} else 
		{
			// interpolate 1 cm array of entire core
			int l = 0;
			m_datptr[l] = valueptrI->getData();
			int target = start_depth + 2;

			l = 1;
			int highfound, lowfound;
			for(int m = i; target < end_depth && l < m_maxdepth; target++,l++)
			{
				// find value >= to target value	
				highfound = lowfound = 0;
				while(m < numvalues && j >= 0 && !(lowfound & highfound))
				{
					valueptrM =  coreptr->getValue(m);
					if(valueptrM == NULL) continue;
					valueptrJ =  coreptr->getValue(j);
					if(valueptrJ == NULL) continue;
	
					if(m_usedepth == 0)
					{
						
						if(!highfound)
						{ 
							if(!(target <= rint((double)(valueptrM->getMbsf() * 100)) && valueptrM->getQuality() == GOOD)) 
							{
								m++;
							} else 
							{
								highfound = 1;
								j = m;
							}
						} else 
						{
							if(!(target > rint((double)(valueptrJ->getMbsf() * 100)) && valueptrJ->getQuality() == GOOD))
							{
								j--;
							} else
							{
								lowfound = 1;
							}
						}
					} else 
					{
						if(!highfound && !(target <= rint((double)(valueptrM->getDepth() * 100)) && valueptrM->getQuality() == GOOD)) 
						{
							m++;
						} else if (!highfound)
						{
							highfound = 1;
							j = m;
						} else 
						{
							if(!(target > rint((double)(valueptrJ->getDepth() * 100)) && valueptrJ->getQuality() == GOOD))
							{
								j--;
							} else
							{
								lowfound = 1;
							}
						}					
					}
				} // end of while statement
				
				if(m >= numvalues || j < 0)
				{
					coreptr->setSmoothStatus(SM_TOOFEWPTS);
					//cout << "too few points..... " << m << " " << numvalues << " " << j << endl;
				} else 
				{
					valueptrM =  coreptr->getValue(m);
					if(m_usedepth == 0)
					{
						if(target == rint((double)(valueptrM->getMbsf() * 100)))       
						{	
							// exact match
							m_datptr[l] = valueptrM->getData();
						} else 
						{	
							// interpolate
							valueptrJ =  coreptr->getValue(j);
							m_datptr[l] = valueptrJ->getData() + (valueptrM->getData() - valueptrJ->getData()) * 
										(target / 100.0 - valueptrJ->getMbsf()) / (valueptrM->getMbsf() - valueptrJ->getMbsf());
						}
					} else 
					{
						if(target == rint((double)(valueptrM->getDepth() * 100)))       
						{	
							// exact match
							m_datptr[l] = valueptrM->getData();
						} else 
						{	
							// interpolate
							valueptrJ =  coreptr->getValue(j);
							m_datptr[l] = valueptrJ->getData() + (valueptrM->getData() - valueptrJ->getData()) * 
										(target / 100.0 - valueptrJ->getDepth()) / (valueptrM->getDepth() - valueptrJ->getDepth());		
						}
					}
				}
			} // end of for statement
			
            if (l > m_maxdepth)
            {
				coreptr->setSmoothStatus(SM_TOOFEWPTS);
#ifdef DEBUG				
				cout << "l > m_maxdepth "  << l << " " << m_maxdepth << endl;
#endif
            }
			
            if (coreptr->getSmoothStatus() == NONE)
            {
				m_datptr[l] = coreptr->getValue(end_cnt)->getData();
              
				// smooth data array 
				// loop through data (first and last "halfwidth" values are same as raw data
				for(i = 0; i < halfwidth; i++)
				{
					m_sm_datptr[i]=m_datptr[i];
				}
				// compute smoothed value
				for( ; i < num_depths - halfwidth; i++)
				{
					m_sm_datptr[i]=0.0;
					l = i - halfwidth + 1;
					for(j = 0; j < m_depth; j++,l++)
					{
						m_sm_datptr[i] += m_datptr[l] * m_weight[j+1];
					}
				}
				
				// loop through last half width values
				for( ; i < num_depths; i++)
				{
					m_sm_datptr[i] = m_datptr[i];
				}
			  
				// fill in real smoothed array
				for(i = 0; i < numvalues; i++)
				{
					valueptrI =  coreptr->getValue(i);
					if(valueptrI == NULL) continue;
					
					if(valueptrI->getQuality() != GOOD)
					{
						valueptrI->setSmoothStatus(SM_BAD_DATA);
					} else
					{
						if(m_usedepth == 0)
						{
							if(rint((double)(valueptrI->getMbsf() * 100.0)) < (start_depth + halfwidth))
							{
								valueptrI->setSmoothStatus(SM_TAIL);
							} else if (rint((double)(valueptrI->getMbsf() * 100.0)) > (end_depth - halfwidth))
							{
								valueptrI->setSmoothStatus(SM_TAIL);
							} else 
							{
								j = (int) (rint((double)(valueptrI->getMbsf() * 100.0)) - start_depth);
								valueptrI->setData(m_sm_datptr[j]);
								valueptrI->setSmoothStatus(SM_OK);
							}
						} else 
						{
							if(rint((double)(valueptrI->getDepth() * 100.0)) < (start_depth + halfwidth))
							{
								valueptrI->setSmoothStatus(SM_TAIL);
							} else if (rint((double)(valueptrI->getDepth() * 100.0)) > (end_depth - halfwidth))
							{
								valueptrI->setSmoothStatus(SM_TAIL);
							} else 
							{
								j = (int) (rint((double)(valueptrI->getDepth() * 100.0)) - start_depth);
								valueptrI->setData(m_sm_datptr[j]);
								valueptrI->setSmoothStatus(SM_OK);
							}
						}
					}
				}
				coreptr->setSmoothStatus(SM_OK);
            } // end of if statement
			
        } // end of if-elseif-else statement
	} // end of if-else statement

}

void GaussianFilter::getGaussWeights(int width, double* weight)
{
	double	power, sum = 0.0;

	double foldwidth = (width - 1.0) / 3.0;
	double halfwidth = (width - 1.0) / 2.0;

	//  compute unscaled weights
	for (int i = 1;  i <= width;  i++)
	{
		power = (halfwidth - (double) i + 1.0) / foldwidth;
		power = -1.0 * power * power;
		weight[i] = exp(power);
		sum += weight[i];
	}

	//  scale weights to add to 1.0
	for (int i = 1;  i <= width;  i++)
	{
		weight[i] /= sum;
	}
}

void GaussianFilter::setWidth( int width )
{
	if(m_weight != NULL) 
	{
		free(m_weight);
		m_weight = NULL;
	}

	// must use an odd number of weights
	if((width % 2) == 0)
	{
		width += 1;
	}
	m_width = width;

	m_weight = (double*) malloc((m_width + 1) * sizeof(double));
	
	getGaussWeights(m_width, m_weight);

	if(m_unit == POINTS)
	{
		if(m_datptr != NULL) 
		{
			free(m_datptr);
			m_datptr = NULL;
		}
		m_datptr = (double*) malloc((m_width + 1) * sizeof(double));
		
		if(m_sm_datptr != NULL) 
		{
			free(m_sm_datptr);
			m_sm_datptr = NULL;
		}
	}
}

int GaussianFilter::getWidth( void )
{
	return m_width;
}

void GaussianFilter::setUnit( int unit )
{
	m_unit = unit;
}

int GaussianFilter::getUnit( void )
{
	return m_unit;
}

void GaussianFilter::setDepth( int depth, int max )
{
	if(m_unit != DEPTH) return;

	if(m_weight != NULL) 
	{
		free(m_weight);
		m_weight = NULL;
	}

	// must use an odd number of weights
	if((depth % 2) == 0)
	{
		depth += 1;
	}
	m_depth = depth;

	m_weight = (double*) malloc((m_depth + 1) * sizeof(double));
	
	getGaussWeights(m_depth, m_weight);

	if(m_datptr != NULL) 
	{
		free(m_datptr);
		m_datptr = NULL;
	}
	///////////////////

	// find max depth -> m to cm
	m_maxdepth = max * 100;

	m_datptr = (double*) malloc((m_maxdepth + 1) * sizeof(double));
		
	if(m_sm_datptr != NULL) 
	{
		free(m_sm_datptr);
		m_sm_datptr = NULL;
	}
	m_sm_datptr = (double*) malloc(m_maxdepth * sizeof(double));

}

int GaussianFilter::getDepth( void )
{
	return m_depth;
}

void GaussianFilter::setPlot( int plot )
{
	m_plot = plot;
}

int GaussianFilter::getPlot( void )
{
	return m_plot;
}
	
void GaussianFilter::useDepth( void )
{
	m_usedepth = 1;
}

void GaussianFilter::useMbsf( void )
{
	m_usedepth = 0;
}
