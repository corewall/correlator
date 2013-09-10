//////////////////////////////////////////////////////////////////////////////////
// CorrelatorLib - Correlator Class Library.  
//
// Module   :  FilterManager.cpp
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

#include <iostream>
#include <FilterManager.h>

using namespace std;

FilterManager::FilterManager( void )
: m_leg(""), m_site(""), m_dataptr(NULL), m_logdataptr(NULL), m_spliceptr(NULL), m_saganptr(NULL)
{ 
}

FilterManager::~FilterManager( void )
{
	init();
}

void FilterManager::init( void )
{
	CullFilter* cullFilter = NULL;
	std::vector<CullFilter*>::iterator iterCull;
	for(iterCull = m_cullFilters.begin(); iterCull != m_cullFilters.end(); iterCull++)
	{
		cullFilter = (CullFilter*) *iterCull;
		delete cullFilter;
		cullFilter = NULL;
	}
	m_cullFilters.clear();

	DecimateFilter* deciFilter = NULL;
	std::vector<DecimateFilter*>::iterator iterDeci;
	for(iterDeci = m_deciFilter.begin(); iterDeci != m_deciFilter.end(); iterDeci++)
	{
		deciFilter = (DecimateFilter*) *iterDeci;
		delete deciFilter;
		deciFilter = NULL;			
	}
	m_deciFilter.clear();	
				
	GaussianFilter* smoothFilter = NULL;
	std::vector<GaussianFilter*>::iterator iterSmooth;
	for(iterSmooth = m_smoothFilter.begin(); iterSmooth != m_smoothFilter.end(); iterSmooth++)
	{
		smoothFilter = (GaussianFilter*) *iterSmooth;
		delete smoothFilter;
		smoothFilter = NULL;			
	}
	m_smoothFilter.clear();
	
	m_dataptr = NULL;	
	m_logdataptr = NULL;	
	m_spliceptr = NULL;
	m_saganptr = NULL;

}

void FilterManager::setData(Data* dataptr)
{
	m_dataptr = dataptr;
}

void FilterManager::setLogData(Data* dataptr)
{
	m_logdataptr =  dataptr;
}

void FilterManager::setSpliceHole(Hole* holeptr)
{
	m_spliceptr = holeptr;
}

void FilterManager::setSaganHole(Hole* holeptr)
{
	m_saganptr = holeptr;
}
	
CullFilter* FilterManager::getCullFilter( const char* leg, const char* site, int type, char* annot )
{	
	if((strcmp(m_leg.c_str(),leg) ==0) || (strcmp(m_site.c_str(), site)==0))
	{
		// delete all cull filters
		init();	
		m_leg = leg;
		m_site = site;
	}

	//cout << "cull filter type = " << type << endl;
	string str_annot = "";
	if (annot != NULL)
	{
		str_annot = annot;
		size_t pos = str_annot.find("All ");
		if (pos !=string::npos)
		{
			pos = pos + 4; 
			str_annot = str_annot.substr(pos);
		}
	}
	
	CullFilter* cullFilter = NULL;
	std::vector<CullFilter*>::iterator iterCull;
	for(iterCull = m_cullFilters.begin(); iterCull != m_cullFilters.end(); iterCull++)
	{
		cullFilter = (CullFilter*) *iterCull;
		if(cullFilter)
		{
			//cout << cullFilter->getCoreType() << endl;
			if((type == USERDEFINEDTYPE) && (cullFilter->getCoreType() == type))
			{
				if(strcmp(cullFilter->getAnnotation(), str_annot.c_str()) == 0)
				{
					//cout << "[DEBUG] found type == user defined " << endl;
					return cullFilter;
				}
			} else if (cullFilter->getCoreType() == type)
			{
					return cullFilter;
			}	
		}
	}
	
	cullFilter = new CullFilter();
	cullFilter->setCoreType(type);
	if ((type == USERDEFINEDTYPE) &&  (annot != NULL))
	{
		cullFilter->setAnnotation(str_annot.c_str());
	}		
	m_cullFilters.push_back(cullFilter);
#ifdef DEBUG	
	cout << "[DEBUG] New cull filter is created : " << type << " " << str_annot.c_str() << endl;
#endif
	return cullFilter;

}

DecimateFilter* FilterManager::getDeciFilter( const char* leg, const char* site, int type, char* annot )
{
	if((strcmp(m_leg.c_str(),leg) ==0) || (strcmp(m_site.c_str(), site)==0))
	{
		// delete all cull filters
		init();	
		m_leg = leg;
		m_site = site;		
	}
	
	string str_annot = "";
	if (annot != NULL)
	{
		str_annot = annot;
		size_t pos = str_annot.find("All ");
		if (pos !=string::npos)
		{
			pos = pos + 4; 
			str_annot = str_annot.substr(pos);
		}
	}
	
	DecimateFilter* deciFilter = NULL;
	std::vector<DecimateFilter*>::iterator iterDeci;
	for(iterDeci = m_deciFilter.begin(); iterDeci != m_deciFilter.end(); iterDeci++)
	{
		deciFilter = (DecimateFilter*) *iterDeci;
		if(deciFilter)
		{
			if((type == USERDEFINEDTYPE) && (deciFilter->getCoreType() == type))
			{
				if(strcmp(deciFilter->getAnnotation(), str_annot.c_str()) == 0)
				{
					//cout << "[DEBUG] found type == user defined " << endl;				
					return deciFilter;
				}
			} else if (deciFilter->getCoreType() == type)
			{
					return deciFilter;
			}		
		}		
	}
	deciFilter = new DecimateFilter();
	deciFilter->setCoreType(type);
	if ((type == USERDEFINEDTYPE) &&  (annot != NULL))
	{
		deciFilter->setAnnotation(str_annot.c_str());
	}
	
	m_deciFilter.push_back(deciFilter);
#ifdef DEBUG	
	cout << "[DEBUG] New deci filter is created : " << str_annot.c_str() << endl;
#endif
	return deciFilter;
}

GaussianFilter* FilterManager::getSmoothFilter( const char* leg, const char* site, int type, char* annot )
{
	if((strcmp(m_leg.c_str(),leg) ==0) || (strcmp(m_site.c_str(), site)==0))
	{
		// delete all cull filters
		init();	
		m_leg = leg;
		m_site = site;	
	}

	string str_annot = "";
	if (annot != NULL)
	{
		str_annot = annot;
		size_t pos = str_annot.find("All ");
		if (pos !=string::npos)
		{
			pos = pos + 4; 
			str_annot = str_annot.substr(pos);
		}	
	}
	
	GaussianFilter* smoothFilter = NULL;
	std::vector<GaussianFilter*>::iterator iterSmooth;
	for(iterSmooth = m_smoothFilter.begin(); iterSmooth != m_smoothFilter.end(); iterSmooth++)
	{
		smoothFilter = (GaussianFilter*) *iterSmooth;
		if(smoothFilter)
		{
			if((type == USERDEFINEDTYPE) && (smoothFilter->getCoreType() == type))
			{
				if(strcmp(smoothFilter->getAnnotation(), str_annot.c_str()) == 0)
				{
					//cout << "[DEBUG] found type == user defined " << endl;				
					return smoothFilter;
				}
			} else if (smoothFilter->getCoreType() == type)
			{
					return smoothFilter;
			}			
		}			
	}

	smoothFilter = new GaussianFilter();
	smoothFilter->setCoreType(type);
	if ((type == USERDEFINEDTYPE) &&  (annot != NULL))
	{
		smoothFilter->setAnnotation(str_annot.c_str());
	}	
	m_smoothFilter.push_back(smoothFilter);
#ifdef DEBUG	
	cout << "[DEBUG] New smooth filter is created : " << str_annot.c_str() << endl;
#endif
	return smoothFilter;		

}

void FilterManager::apply( void )
{
	if(m_dataptr == NULL) return;
	//cout << "apply " << m_deciFilter.size() << ", " << m_cullFilters.size() << ", " << m_smoothFilter.size() << endl;

	m_dataptr->init(QUALITY);
	int holes = m_dataptr->getNumOfHoles();
	Hole* holeptr = NULL;
	
	DecimateFilter* deciFilter = NULL;
	std::vector<DecimateFilter*>::iterator iterDeci;
	for(iterDeci = m_deciFilter.begin(); iterDeci != m_deciFilter.end(); iterDeci++)
	{
		deciFilter = (DecimateFilter*) *iterDeci;
		if(deciFilter)
		{
			if(deciFilter->getEnable() == false) continue;
			if (deciFilter->getCoreType() == ALL)
			{
				m_dataptr->accept(deciFilter);
			} else 
			{		
				for(int i = 0; i < holes; i++)
				{
					holeptr = m_dataptr->getHole(i);
					//cout << "deci : " << deciFilter->getCoreType() << " " << deciFilter->getAnnotation() << " : " << holeptr->getType() << " " << holeptr->getAnnotation() << endl;				
					if((deciFilter->getCoreType() == USERDEFINEDTYPE) && (strcmp(deciFilter->getAnnotation(), holeptr->getAnnotation()) ==0))
					{
						holeptr->accept(deciFilter);
					} else if (holeptr->getType() == deciFilter->getCoreType())
					{
						holeptr->accept(deciFilter);
					}
				}
			}
		}
	}
	
	CullFilter* cullFilter = NULL;
	std::vector<CullFilter*>::iterator iterCull;
	for(iterCull = m_cullFilters.begin(); iterCull != m_cullFilters.end(); iterCull++)
	{
		cullFilter = (CullFilter*) *iterCull;
		if(cullFilter)
		{
			if(cullFilter->getEnable() == false) continue;
			if (cullFilter->getCoreType() == ALL)
			{
				m_dataptr->accept(cullFilter);
#ifdef DEBUG				
				cout << " it is all ---------------" << endl;
#endif
			} else 
			{
				for(int i = 0; i < holes; i++)
				{
					holeptr = m_dataptr->getHole(i);
					if(holeptr->getTopAvailable() == false)
					{
						cullFilter->setCullTop(0.0);
					}
					
					//cout << "cull : " << cullFilter->getCoreType() << " " << cullFilter->getAnnotation() << " : " << holeptr->getType() << " " << holeptr->getAnnotation() << endl;
					if((cullFilter->getCoreType() == USERDEFINEDTYPE) && (strcmp(cullFilter->getAnnotation(), holeptr->getAnnotation()) ==0))
					{
						holeptr->accept(cullFilter);
					} else if (holeptr->getType() == cullFilter->getCoreType())
					{
						holeptr->accept(cullFilter);
					}
				}
			}
		}
	}

	m_dataptr->update();

	GaussianFilter* smoothFilter = NULL;
	std::vector<GaussianFilter*>::iterator iterSmooth;
	for(iterSmooth = m_smoothFilter.begin(); iterSmooth != m_smoothFilter.end(); iterSmooth++)
	{
		smoothFilter = (GaussianFilter*) *iterSmooth;
		if(smoothFilter)
		{
			if(smoothFilter->getEnable() == false) continue;
			if (smoothFilter->getCoreType() == ALL)
			{
				m_dataptr->accept(smoothFilter);
#ifdef DEBUG				
				cout << "[DEBUG] All are applied " << endl;
#endif
				if (m_spliceptr != NULL)
				{
					m_spliceptr->accept(smoothFilter);
					if(m_saganptr != NULL)
					{
						m_saganptr->copyData(m_spliceptr);
					}
#ifdef DEBUG
					cout << "[DEBUG] Spliced record is applied " << endl;
#endif
				}
			} else if (smoothFilter->getCoreType() == SPLICE)
			{
				if (m_spliceptr != NULL)
				{
					m_spliceptr->accept(smoothFilter);
					if(m_saganptr != NULL)
					{
						m_saganptr->copyData(m_spliceptr);
						m_saganptr->accept(smoothFilter);
					}
#ifdef DEBUG					
					cout << "[DEBUG] Spliced record is applied " << endl;
#endif
				}
			} else 
			{		
				for(int i = 0; i < holes; i++)
				{
					holeptr = m_dataptr->getHole(i);
					if (holeptr == NULL) continue;
					
					//cout << "smooth : " << smoothFilter->getCoreType() << " " << smoothFilter->getAnnotation() << " : " << holeptr->getType() << " " << holeptr->getAnnotation() << endl;				
					if((smoothFilter->getCoreType() == USERDEFINEDTYPE) && (strcmp(smoothFilter->getAnnotation(), holeptr->getAnnotation()) ==0))
					{
						holeptr->accept(smoothFilter);
					} else if (holeptr->getType() == smoothFilter->getCoreType())
					{
						holeptr->accept(smoothFilter);
					}
				}
			}
		}
	}	

	m_dataptr->update();

		
	if(m_logdataptr)
	{
		m_logdataptr->init(QUALITY);
		for(iterDeci = m_deciFilter.begin(); iterDeci != m_deciFilter.end(); iterDeci++)
		{
			deciFilter = (DecimateFilter*) *iterDeci;
			if(deciFilter)
			{
				if(deciFilter->getEnable() == false) continue;
				//cout << deciFilter->getCoreType() << " " << LOGTYPE << endl;
				if(deciFilter->getCoreType() == LOGTYPE)
				{
					m_logdataptr->accept(deciFilter);
					break;
				}
			}
		}
		
		for(iterCull = m_cullFilters.begin(); iterCull != m_cullFilters.end(); iterCull++)
		{
			cullFilter = (CullFilter*) *iterCull;
			if(cullFilter)
			{
				if(cullFilter->getEnable() == false) continue;
				if(cullFilter->getCoreType() == LOGTYPE)
				{
					//cout << "culling is applied" << endl;
					m_logdataptr->accept(cullFilter);
					break;
				}		
			}
		}

		m_logdataptr->update();

		for(iterSmooth = m_smoothFilter.begin(); iterSmooth != m_smoothFilter.end(); iterSmooth++)
		{
			smoothFilter = (GaussianFilter*) *iterSmooth;
			if(smoothFilter)
			{
				if(smoothFilter->getEnable() == false) continue;
				if(smoothFilter->getCoreType() == LOGTYPE)
				{
					m_logdataptr->accept(smoothFilter);
					break;
				}		
			}
		}
	
	}
	//correlator.applyFilter(smoothFilter);
}
