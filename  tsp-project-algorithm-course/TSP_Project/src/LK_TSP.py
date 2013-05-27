package it.luigiarpino.kernighanLin;



/**
 * 
 * @author Luigi Lorenzo Arpino [luigiarpino@yahoo.it]
 *
 */
public class LinKernighan 
{
	
	public static void main(String args[]) throws LinKernighanException
	{
		/*
		int[][] matrix={
			    //   0  1  2  3  4  5  6  7
					{0, 0, 1, 0, 0, 0, 0, 0 },// 0
					{0, 0, 1, 0, 0, 0, 0, 0 },// 1
					{1, 1, 0, 1, 1, 0, 0, 0 },// 2
					{0, 0, 1, 0, 0, 0, 0, 0 },// 3
					{0, 0, 1, 0, 0, 1, 1, 1 },// 4
					{0, 0, 0, 0, 1, 0, 0, 0 },// 5
					{0, 0, 0, 0, 1, 0, 0, 0 },// 6
					{0, 0, 0, 0, 1, 0, 0, 0 },// 7
			};
		*/
		int[][] matrix={
			    //   0  1  2  3  4  5  6  7  8
					{0, 0, 0, 1, 0, 0, 0, 0, 1 },// 0
					{0, 0, 0, 0, 1, 0, 1, 1, 1 },// 1
					{0, 0, 0, 0, 0, 1, 1, 0, 0 },// 2
					{1, 0, 0, 0, 0, 0, 0, 0, 1 },// 3
					{0, 1, 0, 0, 0, 0, 0, 1, 0 },// 4
					{0, 0, 1, 0, 0, 0, 1, 0, 0 },// 5
					{0, 1, 1, 0, 0, 1, 0, 0, 1 },// 6
					{0, 1, 0, 0, 1, 0, 0, 0, 0 },// 7
					{1, 1, 0, 1, 0, 0, 1, 0, 0 },// 8
			};
		
		//KPartitioning kp=new KPartitioning(matrix,4);
		LinKernighan lk=new LinKernighan(matrix,4);
		//LinKernighan lk=new LinKernighan(matrix,2);
		
		int[] partizionamento=lk.getPartizionamento();
		int costo = lk.getCosto();
		int costoMaxTaglio= lk.getCostoMaxTaglio();
		int numMaxNodiPerPartizione=lk.getNumMaxNodiPerPartizione();
		System.out.println();
		System.out.println();
		System.out.println("Costo="+costo);
		System.out.println("Costo Max Taglio="+costoMaxTaglio);
		System.out.println("num Max Nodi Per Partizione="+numMaxNodiPerPartizione);
		System.out.println("Partizionamento");
		for(int i=0; i< partizionamento.length ; i++)
	    {
			System.out.print(" "+partizionamento[i]);
	    }
		
		
	}
	private int[] partizionamento;
	private int costo;
	private int costoMaxTaglio;
	private int numeroPartizioni;
	private int numMaxNodiPerPartizione;
	
	/**
	 * 
	 * @param matrice
	 * @param maxNodi
	 * @throws LinKernighanException
	 */
	public LinKernighan(int[][] matrice, int maxNodi) throws LinKernighanException
	{
		// calcolo il numero di partizioni
		
		
		this.numeroPartizioni=(int)(Math.ceil( (double)matrice.length/(double)maxNodi ) );
		int newNodi = this.numeroPartizioni*maxNodi;
		//this.numeroPartizioni=k;
		if ( ! isMatriceSimmetrica(matrice))
		{
			throw new LinKernighanException("The matrix must be simmetrix");
		}
		// controllo la validita di k
		//this.isKvalid(matrice, k);
		int n=matrice.length;
		//int i = n/k;
		if (newNodi == n)
		{
			KPartitioning kpart=new KPartitioning(matrice, this.numeroPartizioni);
			this.costo=kpart.getCosto();
			this.costoMaxTaglio=kpart.getCostoMaxTaglio();
			this.partizionamento= getNewVettore( kpart.getPartizionamento() );
			this.calcolaNumNodiMaxPerPartizione();
		}
		else
		{
			// genero la nuova matrice
			int[][] newMatrix=new int[newNodi][newNodi];
			for(int row=0; row< newNodi; row++)
			{
				for(int col=0; col< newNodi; col++)
				{
					newMatrix[row][col]=0;
				}	
			}
			for(int row=0; row< matrice.length; row++)
			{
				for(int col=0; col< matrice.length; col++)
				{
					newMatrix[row][col]=matrice[row][col];
				}	
			}
			//DEBUG
			/*
			System.out.println("k="+k);
			System.out.println("newMatrix.length="+newMatrix.length);
			*/
			
			//DEBUG
			KPartitioning kpart=new KPartitioning(newMatrix, this.numeroPartizioni);
			this.costo=kpart.getCosto();
			this.costoMaxTaglio=kpart.getCostoMaxTaglio();
			int[] parti = kpart.getPartizionamento();
			this.partizionamento=new int[matrice.length];
			for (int index=0; index<matrice.length; index++)
			{
				this.partizionamento[index]=parti[index];
			}
			this.calcolaNumNodiMaxPerPartizione();
		}
			
	}

	public int getCosto() 
	{
		return costo;
	}

	public int getCostoMaxTaglio()
	{
		return this.costoMaxTaglio;
	}
	
	private int[] getNewVettore(int[] vett)
	{
		int[] result=new int[vett.length];
		for (int i=0;i<vett.length;i++)
		{
			result[i]=vett[i];
		}
		return result;
	}
	
	public int[] getPartizionamento() 
	{
		return partizionamento;
	}
	
	public int getNumMaxNodiPerPartizione()
	{
		return this.numMaxNodiPerPartizione;
	}
	
	private void isKvalid(int[][] matrix, int k) throws LinKernighanException
	{
		if (k<=0)
		{
			throw new LinKernighanException("K must be > 0 !");
		}
		if (k>matrix.length)
		{
			throw new LinKernighanException("K="+k+" not valid!");
		}
			 
	}
	
	private boolean isMatriceSimmetrica(int[][] matrice)
	{
		/*
		for(int row=0; row< matrice.length; row++)
		{
			for(int col=0; col< matrice.length; col++)
			{
				if (matrice[row][col] !=  matrice[col][row])
				{
					return false;
				}
			}	
		}
		*/
		return true;
	}
	
	
	/**
	 * Calcola il numero massimo di nodi che appartengono ad una partizione
	 */
	private void calcolaNumNodiMaxPerPartizione()
	{
		int result =0;
		for(int set=0; set<this.numeroPartizioni; set++)
		{
			int numNodi=getNumNodiOfSet(set);
			if (numNodi>result)
			{
				result=numNodi;
			}
		}
		this.numMaxNodiPerPartizione=result;
	}
	
	/**
	 * Restituisce il numero di nodi che fanno parte di una partizione
	 * 
	 * @param set
	 * @return
	 */
	private int getNumNodiOfSet(int set)
	{
		int result =0;
		for(int i=0; i<this.partizionamento.length; i++)
		{
			if(this.partizionamento[i] == set)
			{
				result++;
			}
		}
		return result;
	}
	
}
