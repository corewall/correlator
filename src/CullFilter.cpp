//////////////////////////////////////////////////////////////////////////////////
// CorrelatorLib - Correlator Class Library.  
//
// Module   :  CullFilter.cpp
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
#include <iostream>

#include <CoreTypes.h>
#include <CullFilter.h>
#include <Value.h>
#include <Core.h>
#include <Hole.h>
#include <PwaveValue.h>

using namespace std;

CullFilter::CullFilter( double top )
: m_top(top), m_count(0), m_appliedType(""), 
  m_byNumber(-1), m_method(CULL_PARAMETERS),
  m_signalMax(0), m_userEquation(false), m_fptr(NULL)
{
	init();
	if((m_method == CULL_PARAMETERS) || (m_method == CULL_PARAMETER_AND_TABLE))
	{

#ifdef DEBUG
	//cout << "[CullFilter] Culling will be done with user set parameters. Top " << m_top << " cm wil be removed from core." << endl;
#endif
	}
}


CullFilter::CullFilter( char* filename )
: m_top(5.0), m_count(0), m_appliedType(""), 
  m_byNumber(-1), m_method(CULL_PARAMETERS),
  m_signalMax(0), m_userEquation(false), m_fptr(NULL)
{
	init();
	if(create(filename) == 1)
	{
		m_method = CULL_TABLE;
	}	
}

CullFilter::~CullFilter( void )
{
	destory();
}

void CullFilter::init( void )
{
	m_datatype = VALUE;
	
	m_gra.m_sign[0] = LESS_THAN_OR_EQUAL_TO;
	m_gra.m_sign[1] = GREATER_THAN_OR_EQUAL_TO;	
	m_gra.m_join = OR;
	m_gra.m_value[0] = 1.0;
	m_gra.m_value[1] = 2.8;

	m_pwave.m_sign[0] = LESS_THAN;
	m_pwave.m_sign[1] = GREATER_THAN_OR_EQUAL_TO;	
	m_pwave.m_join = ONLY;
	m_pwave.m_value[0] = 0.0;
	m_pwave.m_value[1] = 255;	
	m_signalMax = 167.0;

	m_susceptibility.m_sign[0] = LESS_THAN;
	m_susceptibility.m_sign[1] = GREATER_THAN;	
	m_susceptibility.m_join = ONLY;
	m_susceptibility.m_value[0] = -99999.0;
	m_susceptibility.m_value[1] = 99999.0;	

	m_naturalgamma.m_sign[0] = LESS_THAN;
	m_naturalgamma.m_sign[1] = GREATER_THAN_OR_EQUAL_TO;	
	m_naturalgamma.m_join = ONLY;
	m_naturalgamma.m_value[0] = 0.0;
	m_naturalgamma.m_value[1] = 99999.0;	

	m_reflectance.m_sign[0] = LESS_THAN_OR_EQUAL_TO;
	m_reflectance.m_sign[1] = GREATER_THAN_OR_EQUAL_TO;	
	m_reflectance.m_join = OR;
	m_reflectance.m_value[0] = 0.0;
	m_reflectance.m_value[1] = 100.0;
	
	m_otherodp.m_sign[0] = LESS_THAN;
	m_otherodp.m_sign[1] = GREATER_THAN;	
	m_otherodp.m_join = OR;
	m_otherodp.m_value[0] = -99999.0;
	m_otherodp.m_value[1] = 99999.0;	
	
	m_fptr = NULL;
	m_enable =false;
	destory();	
}

void CullFilter::visitor( CoreObject* object )
{
	if(m_enable == false) return;
	if(m_method == -1) return;
	
	Value* valueptr = (Value*) object;
	Core* coreptr = NULL;
	Hole* holeptr = NULL;
	
	int quality = valueptr->getQuality();
	
	//cout << valueptr->getType() << " - " << valueptr->getValueType() << " - " << m_coretype << std::endl;
	//if ((m_coretype != ALL) && (valueptr->getValueType() != m_nType))
	if (m_coretype == USERDEFINEDTYPE)
	{
		coreptr = (Core*) valueptr->getParent();
		holeptr = (Hole*) coreptr->getParent();
		//cout << "[ERRPR] Annotation =" <<  m_annotation << " , " <<  holeptr->getAnnotation() << endl;
		if (m_annotation != holeptr->getAnnotation())
		{
			//cout << "[ERRPR] Annotation =" <<  m_annotation << " , " <<  holeptr->getAnnotation() << endl;
			return;
		}
	}
	else if ((m_coretype != ALL) && (m_coretype != LOGTYPE) && (valueptr->getValueType() != m_coretype))
	{
		//cout << "[ERRPR] " << m_appliedType << " " << m_coretype << " : " << valueptr->getValueType() << " is skipped "  << endl;
		return;
	}
	
	//if(m_coretype != valueptr->getValueType())
	//	cout << m_coretype << " " << valueptr->getValueType() << endl;

	//cout << "m_top : " << m_top << endl;
	// remove top portion of core
	if((strcmp(valueptr->getSection(), "1") == 0) && (valueptr->getTop() < m_top))
	{
		quality = quality | BAD_TOP;
	}
	
	// remove cores > given number
	if(m_byNumber >= 0 )	
	{
		// BUG
		int coreNumber = valueptr->getCoreNumber(); 
		if(coreNumber >= 0 && (m_byNumber < coreNumber) ) 
		{
			quality = quality | BAD_CORE_NUM;
		}
	}

	if((m_method == CULL_PARAMETERS) || (m_method == CULL_PARAMETER_AND_TABLE))
	{
		//cout << "cull parameters" << endl;
			
		int type = valueptr->getValueType();
		double data = valueptr->getData();
		if(m_userEquation == true) 
		{
			quality = quality | evalEquation(data, &m_cull_equation);
		} else 
		{	
			switch(type)
			{
			case GRA :
					quality = quality | evalEquation(data, &m_gra);					
					break;
			case PWAVE :
					{
						quality = quality | evalEquation(data, &m_pwave);
						int format = valueptr->getDataFormat();					
						if(format == MST95REPORT) 
						{
							PwaveValue* pwvalueptr = (PwaveValue*) valueptr;
							if(pwvalueptr->getStrength() < m_signalMax)
							{
								quality = quality | BAD_PWAVE_SIGNAL;
							}
						}
					}
					break;
			case SUSCEPTIBILITY :
					quality = quality | evalEquation(data, &m_susceptibility);					
					break;
			case NATURALGAMMA :
					quality = quality | evalEquation(data, &m_naturalgamma);					
					break;
			case REFLECTANCE :
					quality = quality | evalEquation(data, &m_reflectance);					
					break;
			case OTHERTYPE :
					quality = quality | evalEquation(data, &m_otherodp);					
					break;
			default:
					quality = quality | evalEquation(data, &m_otherodp);					
			}
		}
	} 
	
	if((m_method == CULL_TABLE) || (m_method == CULL_PARAMETER_AND_TABLE))
	{
		//cout << "cull table " << endl;
		
		int hashsize = m_hashtable.size();
		//cout << "hash table " << hashsize << endl;
		for(int i = 0; i < hashsize; i++)
		{
			//cout << "start -test " << m_hashtable[i]->m_leg << " " << m_hashtable[i]->m_site << " " <<  m_hashtable[i]->m_hole << " " <<  m_hashtable[i]->m_core << " " << m_hashtable[i]->m_section[0] << endl;
			//if(valueptr->check(m_hashtable[i]->m_leg, m_hashtable[i]->m_site, m_hashtable[i]->m_hole, m_hashtable[i]->m_core, &m_hashtable[i]->m_section[0]) == 1)
			if(valueptr->check((char*)m_hashtable[i]->m_leg.c_str(), (char*)m_hashtable[i]->m_site.c_str(), (char*)m_hashtable[i]->m_hole.c_str(), m_hashtable[i]->m_core, NULL) == 1)
			{
			    
				if((m_hashtable[i]->m_badcore == true) && (m_fptr == NULL))
				{
					coreptr = (Core*) valueptr->getParent();
					if(coreptr->getQuality() != BAD)
					{
						coreptr->setQuality(BAD);
					}
				}
				//cout << "top : " << valueptr->getTop() << " : " << m_hashtable[i]->m_top << endl;
				else if (fabs(valueptr->getTop() - m_hashtable[i]->m_top) <= CULL_TABLE_DEPTH_CHECK)
				{
					//cout << "inside = " << i  << endl;
					quality = quality | BAD_CULLTABLE;
					break;
				}
			}
		}
	}

	valueptr->setQuality(quality);
	if(quality != GOOD) 
	{
		++m_count;
	}	
	
	if(m_fptr != NULL)
	{
		int flag=BAD_CULL1 | BAD_CULL2 | BAD_TOP | BAD_CULLTABLE;
		coreptr = (Core*) valueptr->getParent();
		if (coreptr != NULL) 
		{
			//cout << valueptr->getNumber() << " " << coreptr->getQuality() << " " << coreptr->getName() << " " << coreptr->getNumber() << endl;
			if((valueptr->getNumber() == 0) && (coreptr->getQuality() == BAD))
			{
				//cout << "bad " << endl;
				fprintf (m_fptr, "%s \t%s \t%s \t%d \tbadcore \t\n", coreptr->getLeg(), coreptr->getSite(), coreptr->getName(), coreptr->getNumber());			
			}
			if(quality & flag)
			{
				// leg, site, holename, coreno, coretype, section, bottom, top, 
				fprintf (m_fptr, "%s \t%s \t%s \t%d \t%c \t%s \t%.2f \t%.2f \t\n", 
					coreptr->getLeg(), coreptr->getSite(), coreptr->getName(), coreptr->getNumber(),
					valueptr->getType(), valueptr->getSection(), valueptr->getBottom(), valueptr->getTop());
			}
		} 
	} 
}

int CullFilter::create( char* filename)
{

	FILE *fptr= fopen(filename,"r+");
	if(fptr == NULL) 
	{
#ifdef DEBUG	
		cout << "[ERROR] cullfilter " << filename << " could not be opened " << endl;
#endif
		return -1;
	}
	
	HashInfo* infoptr = NULL;
	int ret;
	double bottom;
	double top;
	int count =0;
	//cout << " loading cull data" << endl;
	char badcore[10];
	char token[10];
	char line[MAX_LINE];
	memset(line, 0, MAX_LINE);
	char sign0, sign1;
	size_t pos;
	bool equation_info = false;
	char leg[16];
	char site[16];
	bool universal_cull = false;
	int coretype;
		
	while(true)
	{
		if(fgets(line, MAX_LINE, fptr) == NULL) break;
		//cout << "line : " << line << endl;
		if(line[0] == '#') 
		{
			ret = sscanf (line, "# %s", &token[0]);
			if(strcmp(token, "Top") == 0)
			{
				ret = sscanf (line, "# Top %f", &m_top);
#ifdef DEBUG				
				cout << "[DEBUG] Cull top: " << m_top << endl;
#endif
			} else if (strcmp(token, "Range") == 0)
			{
				float x, y;
				ret = sscanf (line, "# Range %c %f %c %f", &sign0, &x, &sign1, &y);
				m_cull_equation.m_value[0] = x;
				m_cull_equation.m_value[1] = y;
				if(ret >= 2) 
				{
					if(sign0 == '<')
						m_cull_equation.m_sign[0] = LESS_THAN;
					else if (sign0 == '>')
						m_cull_equation.m_sign[0] = GREATER_THAN;
#ifdef DEBUG						
					cout << "[DEBUG] Cull range: " << m_cull_equation.m_value[0] << " " <<  sign0 << " " << m_cull_equation.m_sign[0] << endl;	
#endif
					m_cull_equation.m_join = ONLY;
				} 
				if(ret == 4)
				{
					if(sign1 == '<')
						m_cull_equation.m_sign[1] = LESS_THAN;
					else if (sign1 == '>')
						m_cull_equation.m_sign[1] = GREATER_THAN;
#ifdef DEBUG						
					cout << "[DEBUG] " << m_cull_equation.m_value[1] << " " << sign1 << " " << m_cull_equation.m_sign[1] << endl;	
#endif
					m_cull_equation.m_join = OR;
				}
				equation_info= true;
				
			} else if (strcmp(token, "Core") == 0)
			{
				ret = sscanf (line, "# Core %d", &m_byNumber);
#ifdef DEBUG				
				cout << "[DEBUG] Cull coore no : " << m_byNumber << endl;
#endif
			} else if (strcmp(token, "Type") == 0)
			{
				//char type_buff[125];
				//ret = sscanf (line, "# Type %s", &type_buff[0]);
				m_appliedType =  line;
				pos = m_appliedType.find("# Type ");
				if (pos !=string::npos)
				{
					pos = pos + 7; 
					m_appliedType = m_appliedType.substr(pos);
					pos = m_appliedType.find("\n");
					m_appliedType.erase (pos);
				}
		
				// TEMPORARILY... BLOCKED
				if (m_appliedType == "GRA")
					coretype = GRA; 
				else if (m_appliedType == "Bulk")
					coretype = GRA; 
				else if (m_appliedType == "Bulk Density(GRA)")
					coretype = GRA; 
				else if (m_appliedType == "Pwave")
					coretype = PWAVE;
				else if (m_appliedType == "PWave")
					coretype = PWAVE;
				else if (m_appliedType == "Susceptibility")
					coretype = SUSCEPTIBILITY;					
				else if (m_appliedType == "NaturalGamma")
					coretype = NATURALGAMMA;					
				else if (m_appliedType == "Natural Gamma")
					coretype = NATURALGAMMA;	
				else if (m_appliedType == "Reflectance")
					coretype = REFLECTANCE;	
				else if (m_appliedType == "OtherType")
					coretype = OTHERTYPE;
				else if (m_appliedType == "Log")
					coretype = LOGTYPE;					
				else {
					coretype = USERDEFINEDTYPE;	
					setAnnotation(m_appliedType);
				}
				//cout << " m_appliedType=" << m_appliedType  << " " << coretype << " m_coretype=" << m_coretype << endl;
				 

				if (coretype != m_coretype)
				{
					universal_cull = true;
#ifdef DEBUG					
					std::cout << "[DEBUG] Cull Data type is different " << std::endl;
#endif
				} else 
				{
#ifdef DEBUG				
					std::cout << "[DEBUG] Cull type : " << m_appliedType.c_str() << " " << std::endl;
#endif
				}
			}

			continue;
		}

		ret = sscanf (line, "%s %s", &leg, &site);
		//cout << "[DEBUG] leg= " << leg << " site= " << site << endl;
		break;
		// BLOCK
		/*infoptr = new HashInfo;
		infoptr->m_badcore = false;
		
		ret = sscanf (line, "%d %d  %c  %d %s %s %f %f\n", &infoptr->m_leg, &infoptr->m_site, &infoptr->m_hole, &infoptr->m_core, &badcore[0], &infoptr->m_section, &bottom, &top);
		// BLOCK
		if(ret <= 0)
		{
			delete infoptr;
			break;
		}
		
		if((ret == 5) && (strcmp(badcore, "badcore") == 0))
		{
			infoptr->m_badcore = true;
			//cout << "badcore -----------" << endl;
		} else 
		{
			//ret = fscanf (fptr, "%d %d  %c  %d %c %s  %f %f\n", 
			//		&infoptr->m_leg, &infoptr->m_site, &infoptr->m_hole, &infoptr->m_core,
			//		&infoptr->m_type, &infoptr->m_section, &bottom, &top);
			infoptr->m_type = badcore[0];
			infoptr->m_top = top;
			//cout << " 1 " << ret << " " << infoptr->m_leg << " " << infoptr->m_site << " " << infoptr->m_hole << " " << infoptr->m_core<< " ";
			//cout << infoptr->m_type << " " << infoptr->m_section << " " << bottom << " " << top << endl;
		}
		
		m_hashtable.push_back(infoptr);
		*/
		count++;
	}
			
	if(ret <= 0)
	{
		equation_info = false;
	}
	if(universal_cull == true)
	{
		equation_info = false;
	}
	
	m_method = CULL_TABLE;
	if (equation_info == true)
	{
		m_method = CULL_PARAMETERS;
		m_userEquation = true;
#ifdef DEBUG		
		cout << "[Cull] " << filename <<  " : " <<  " culling info was loaded successfully.(parameter) : " << endl; 
#endif
		fclose(fptr);
		return 0;
	} 
#ifdef DEBUG	
	cout << "[Cull] " << filename <<  " : " <<  " culling info was loaded successfully.(table) : " << endl; 
#endif
	fclose(fptr);
	return 1;
}

int CullFilter::openCullTable( char* filename, char* type )
{
	m_fptr= fopen(filename,"w+");
	if(m_fptr == NULL) 
	{
#ifdef DEBUG	
		cout << "[ERROR] cullfilter " << filename << " could not be opened " << endl;
#endif
		return 0;
	}
#ifdef DEBUG	
	cout <<  "[Cull] " << filename << " is opened for save" << endl; 
#endif
		
	fprintf (m_fptr, "# Leg Site Hole Core No Section_Type Section_No Top Bottom\n");
	fprintf (m_fptr, "# Leg Site Hole Core No badcore\n");
	
	fprintf (m_fptr, "# Top %.3f\n", m_top);
	
	if (m_cull_equation.m_value[0] < 9999.00)
	{
		int range_flag = 0;
		if (m_cull_equation.m_sign[0] == LESS_THAN)
		{
			fprintf (m_fptr, "# Range < %.3f", m_cull_equation.m_value[0]);
			range_flag = 1;
		} else if (m_cull_equation.m_sign[0] == GREATER_THAN)
		{
			fprintf (m_fptr, "# Range > %.3f", m_cull_equation.m_value[0]);
			range_flag = 1;
		}
		
		if(m_cull_equation.m_join == OR)
		{
			if (m_cull_equation.m_sign[1] == LESS_THAN)
			{
				fprintf (m_fptr, " < %.3f", m_cull_equation.m_value[1]);
			} else if (m_cull_equation.m_sign[1] == GREATER_THAN)
			{
				fprintf (m_fptr, " %.3f", m_cull_equation.m_value[1]);
			}
		}
		if (range_flag == 1)
			fprintf (m_fptr, "\n");
	
	if(m_byNumber > 0)
	{
		fprintf (m_fptr, "# Core %d\n", m_byNumber);
	}
	}
	
	m_appliedType = type;
	/*if (m_appliedType == "Bulk Density(GRA)")
		m_coretype = GRA;
	if (m_appliedType == "GRA")
		m_coretype = GRA; 
	else if (m_appliedType == "Pwave")
		m_coretype = PWAVE;
	else if (m_appliedType == "PWave")
		m_coretype = PWAVE;
	else if (m_appliedType == "Susceptibility")
		m_coretype = SUSCEPTIBILITY;					
	else if (m_appliedType == "NaturalGamma")
		m_coretype = NATURALGAMMA;					
	else if (m_appliedType == "Reflectance")
		m_coretype = REFLECTANCE;	
	else if (m_appliedType == "OtherType")
		m_coretype = OTHERTYPE;
	else if (m_appliedType == "Log")
		m_coretype = LOGTYPE;					
	else 
		m_coretype = USERDEFINEDTYPE;
	*/		
	fprintf (m_fptr, "# Type %s\n", m_appliedType.c_str());
		
	fprintf (m_fptr, "# Generated By Correlator\n");

	
	return 1;
}

int CullFilter::closeCullTable( void )
{
	if(m_fptr != NULL) 
	{
		fclose(m_fptr);
		m_fptr = NULL;
		return 1;	
	}
	return 0;
}

void CullFilter::destory( void )
{
	HashInfo* infoptr= NULL;
	int hashsize = m_hashtable.size();
	for(int i = 0; i < hashsize; i++)
	{
		infoptr = (HashInfo*) m_hashtable[i]; 
		delete infoptr;
		infoptr = NULL;
	}
	m_hashtable.clear();
		
}

int	CullFilter::evalEquation(double data, Equation* cull_equation)
{
	int qual1,qual2,qual;
	qual1=qual2=qual=GOOD;

	if((cull_equation->m_sign[0] == LESS_THAN) && (data < cull_equation->m_value[0]))
	{
		qual1 =BAD_CULL1;
	} else if ((cull_equation->m_sign[0] == LESS_THAN_OR_EQUAL_TO) && (data <= cull_equation->m_value[0]))
	{
		qual1 =BAD_CULL1;
	} else if ((cull_equation->m_sign[0] == GREATER_THAN) && (data > cull_equation->m_value[0]))
	{
		qual1 =BAD_CULL1;
	} else if ((cull_equation->m_sign[0] == GREATER_THAN_OR_EQUAL_TO) && (data >= cull_equation->m_value[0]))
	{
		qual1 =BAD_CULL1;
	} else if ((cull_equation->m_sign[0] == EQUAL_TO) && (data == cull_equation->m_value[0]))
	{
		qual1 =BAD_CULL1;
	}
	
	if(cull_equation->m_join == ONLY)
	{
		qual=qual1;
	} else
	{
		if((cull_equation->m_sign[1] == LESS_THAN) && (data < cull_equation->m_value[1]))
		{
			qual2 =BAD_CULL2;
		} else if ((cull_equation->m_sign[1] == LESS_THAN_OR_EQUAL_TO) && (data <= cull_equation->m_value[1]))
		{
			qual2 =BAD_CULL2;
		} else if ((cull_equation->m_sign[1] == GREATER_THAN) && (data > cull_equation->m_value[1]))
		{
			qual2 =BAD_CULL2;
		} else if ((cull_equation->m_sign[1] == GREATER_THAN_OR_EQUAL_TO) && (data >= cull_equation->m_value[1]))
		{
			qual2 =BAD_CULL2;
		} else if ((cull_equation->m_sign[1] == EQUAL_TO) && (data == cull_equation->m_value[1]))
		{
			qual2 =BAD_CULL2;
		}
		
		if(cull_equation->m_join == OR)
		{
			qual=qual1|qual2;
		}
	}
	return(qual);
}

bool CullFilter::isUserEquation( void )
{
	return m_userEquation;
}

Equation* CullFilter::getEquation( void )
{
	return &m_cull_equation;
}	

void CullFilter::setEquation( double value1, double value2, int sign1, int sign2, int join )
{
	m_userEquation= true;
	m_cull_equation.m_value[0] = value1;
	m_cull_equation.m_value[1] = value2;
	m_cull_equation.m_join = ONLY;
	if (join == 2) 
		m_cull_equation.m_join = OR;
	m_cull_equation.m_sign[0] = GREATER_THAN;
	if(sign1 == 2)
		m_cull_equation.m_sign[0] = LESS_THAN;
	m_cull_equation.m_sign[1] = GREATER_THAN;
	if(sign2 == 2)
		m_cull_equation.m_sign[1] = LESS_THAN;
#ifdef DEBUG		
	cout << "[DEBUG] Set equation " << value1 << " " << sign1 << " " << m_cull_equation.m_sign[0] << " " << m_annotation.c_str() << endl;
#endif
}

int	CullFilter::evalEquationAlt(double data, Equation* cull_equation)
{
	int qual;
	qual=0;

	if((cull_equation->m_sign[0] == LESS_THAN) && (data < cull_equation->m_value[0]))
	{
		qual = 1;
	} else if ((cull_equation->m_sign[0] == LESS_THAN_OR_EQUAL_TO) && (data <= cull_equation->m_value[0]))
	{
		qual = 1;
	} else if ((cull_equation->m_sign[0] == GREATER_THAN) && (data > cull_equation->m_value[0]))
	{
		qual = 1;
	} else if ((cull_equation->m_sign[0] == GREATER_THAN_OR_EQUAL_TO) && (data >= cull_equation->m_value[0]))
	{
		qual = 1;
	} else if ((cull_equation->m_sign[0] == EQUAL_TO) && (data == cull_equation->m_value[0]))
	{
		qual = 1;
	}
	
	if(cull_equation->m_join == ONLY) 
	{
	} else
	{
		if((cull_equation->m_sign[1] == LESS_THAN) && (data < cull_equation->m_value[1]))
		{
			qual = 1;
		} else if ((cull_equation->m_sign[1] == LESS_THAN_OR_EQUAL_TO) && (data <= cull_equation->m_value[1]))
		{
			qual = 1;
		} else if ((cull_equation->m_sign[1] == GREATER_THAN) && (data > cull_equation->m_value[1]))
		{
			qual = 1;
		} else if ((cull_equation->m_sign[1] == GREATER_THAN_OR_EQUAL_TO) && (data >= cull_equation->m_value[1]))
		{
			qual = 1;
		} else if ((cull_equation->m_sign[1] == EQUAL_TO) && (data == cull_equation->m_value[1]))
		{
			qual = 1;
		}
	}

	if(qual == 0) 
	{
		return(0);
	}
	
	return(LOG_VALUE_CULLED);
}

void CullFilter::setCullTop( int top )
{
	m_top = top;
}

int	CullFilter::getCullTop( void )
{
	return m_top;
}

void CullFilter::setCullCoreNo( int number )
{
	m_byNumber = number;
}

int CullFilter::getCullCoreNo( void )
{
	return m_byNumber;
}

void CullFilter::setCullSignal( int signal )
{
	m_signalMax = signal;
}

int CullFilter::getCullSignal( void )
{
	return m_signalMax;
}

void CullFilter::setMethod( int method )
{
	m_method = method;
}

int CullFilter::getMethod( void )
{
	return m_method;
}
